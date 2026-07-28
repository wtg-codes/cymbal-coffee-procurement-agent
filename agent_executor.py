"""Agent executor for ADK agents adapted for A2A compatibility on Agent Engine."""

import logging

from a2a import types, utils
from a2a.server import agent_execution, events, tasks
from a2a.utils import errors as a2a_errors
from google.adk import runners
from google.adk.artifacts import in_memory_artifact_service
from google.adk.memory import in_memory_memory_service
from google.adk.sessions import in_memory_session_service
from google.genai import types as genai_types

from app import agent as app_agent

# Protobuf setstate patch for Python compatibility
try:
    from google.protobuf.message import Message

    original_setstate = Message.__setstate__

    def patched_setstate(self, state):
        if "serialized" not in state:
            state["serialized"] = b""
        return original_setstate(self, state)

    Message.__setstate__ = patched_setstate
except Exception:
    pass

logger = logging.getLogger(__name__)


class AdkAgentToA2AExecutor(agent_execution.AgentExecutor):
    """An agent executor for ADK agents to make them A2A compatible."""

    def __init__(self):
        self._agent = app_agent.root_agent
        self._runner = runners.Runner(
            app_name=self._agent.name,
            agent=self._agent,
            session_service=in_memory_session_service.InMemorySessionService(),
            artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
            memory_service=in_memory_memory_service.InMemoryMemoryService(),
        )
        self._user_id = "remote_agent"

    async def execute(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task
        logger.info("[DEBUG] Query: %s", query)

        if not task:
            if not context.message:
                return

            task = utils.new_task(context.message)
            await event_queue.enqueue_event(task)

        updater = tasks.TaskUpdater(event_queue, task.id, task.context_id)
        session_id = task.context_id

        session = await self._runner.session_service.get_session(
            app_name=self._agent.name,
            user_id=self._user_id,
            session_id=session_id,
        )
        if session is None:
            session = await self._runner.session_service.create_session(
                app_name=self._agent.name,
                user_id=self._user_id,
                state={},
                session_id=session_id,
            )

        await updater.start_work()

        content = genai_types.Content(role="user", parts=[{"text": query}])

        final_response_content = ""

        try:
            async for event in self._runner.run_async(
                user_id=self._user_id, session_id=session.id, new_message=content
            ):
                if event.is_final_response():
                    if (
                        event.content
                        and event.content.parts
                        and event.content.parts[0].text
                    ):
                        final_response_content += event.content.parts[0].text

        except Exception as e:
            await updater.failed(
                message=utils.new_agent_text_message(
                    f"Task failed with error: {e!s}"
                )
            )
            return

        if not final_response_content:
            await updater.failed(
                message=utils.new_agent_text_message("No response generated.")
            )
            return

        from app.a2ui_config import format_a2ui_parts

        parts = format_a2ui_parts(final_response_content)
        await updater.add_artifact(parts, name="response")
        await updater.complete()

    async def cancel(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        raise a2a_errors.ServerError(error=types.UnsupportedOperationError())
