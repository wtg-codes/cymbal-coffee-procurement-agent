# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Attach A2A (Agent2Agent) endpoints to the FastAPI app.

func:`attach_a2a_routes` registers the dynamic
agent-card endpoint and the JSON-RPC endpoint so the same app serves A2A
alongside the adk_api routes, reachable by A2A clients and Gemini Enterprise A2A
registration.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from a2a import types, utils
from a2a.server import agent_execution, events, tasks
from a2a.server.apps import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import TaskStore
from a2a.types import AgentCapabilities, AgentExtension
from a2a.utils import errors as a2a_errors
from a2a.utils.constants import (
    AGENT_CARD_WELL_KNOWN_PATH,
    EXTENDED_AGENT_CARD_PATH,
)
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.genai import types as genai_types

if TYPE_CHECKING:
    from fastapi import FastAPI
    from google.adk.agents import BaseAgent
    from google.adk.runners import Runner

# URI advertised on the agent card describing the executor extension shipped
# by ADK. Kept as a module-level constant so callers can override or extend
# the capabilities list when needed.
_ADK_AGENT_EXECUTOR_EXTENSION_URI = (
    "https://google.github.io/adk-docs/a2a/a2a-extension/"
)


def _default_capabilities() -> AgentCapabilities:
    """Returns the default A2A capabilities used by scaffolded projects."""
    # Import A2UI extensions to advertise declarative UI support
    from app.a2ui_config import get_a2ui_extensions

    return AgentCapabilities(
        streaming=True,
        extensions=[
            AgentExtension(
                uri=_ADK_AGENT_EXECUTOR_EXTENSION_URI,
                description=("Ability to use the new agent executor implementation"),
            ),
            *get_a2ui_extensions(),
        ],
    )


logger = logging.getLogger(__name__)


class CustomA2aAgentExecutor(agent_execution.AgentExecutor):
    """Executor that intercepts LLM text and A2UI DataParts and streams them to Gemini Enterprise as A2A Part messages."""

    def __init__(self, agent: BaseAgent, runner: Runner):
        self._agent = agent
        self._runner = runner
        self._user_id = "remote_agent"

    async def execute(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        query = context.get_user_input()
        task = context.current_task

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

        text_chunks: list[str] = []
        data_parts: list[types.Part] = []

        try:
            async for event in self._runner.run_async(
                user_id=self._user_id, session_id=session.id, new_message=content
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            t = part.text.strip()
                            if t and t != "\u200b" and t not in text_chunks:
                                text_chunks.append(t)
                        elif hasattr(part, "inline_data") and part.inline_data:
                            blob = part.inline_data.data
                            if isinstance(blob, bytes):
                                blob_str = blob.decode("utf-8", errors="ignore")
                                import json
                                import re
                                matches = re.findall(
                                    r"<a2a_datapart_json>(.*?)</a2a_datapart_json>",
                                    blob_str,
                                    re.DOTALL,
                                )
                                for match_str in matches:
                                    try:
                                        raw_data = json.loads(match_str)
                                        a2ui_msg = raw_data.get("data", raw_data)
                                        mime_type = raw_data.get("metadata", {}).get(
                                            "mimeType", "application/json+a2ui"
                                        )
                                        data_parts.append(
                                            types.Part(
                                                root=types.DataPart(
                                                    data=a2ui_msg,
                                                    metadata={"mimeType": mime_type},
                                                )
                                            )
                                        )
                                    except Exception as ex:
                                        logger.warning(
                                            "Failed to parse A2UI DataPart blob in A2A executor: %s",
                                            ex,
                                        )
        except Exception as e:
            await updater.failed(
                message=utils.new_agent_text_message(
                    f"Task failed with error: {e!s}"
                )
            )
            return

        a2a_parts: list[types.Part] = []

        if text_chunks:
            import re
            clean_summary = "\n\n".join(text_chunks)
            clean_summary = re.sub(r"</?a2a_datapart_json>", "", clean_summary)
            clean_summary = re.sub(r"<a2ui-json>.*?</a2ui-json>", "", clean_summary, flags=re.DOTALL)
            clean_summary = re.sub(r"```(?:json)?.*", "", clean_summary, flags=re.DOTALL).strip()
            if clean_summary:
                a2a_parts.append(types.Part(root=types.TextPart(text=clean_summary)))

        a2a_parts.extend(data_parts)

        # Fallback if no inline_data DataParts were captured
        if not data_parts and text_chunks:
            from app.a2ui_config import format_a2ui_parts
            a2a_parts = format_a2ui_parts("\n\n".join(text_chunks))

        if not a2a_parts:
            await updater.failed(
                message=utils.new_agent_text_message("No response generated.")
            )
            return

        response_message = utils.new_agent_parts_message(a2a_parts)
        await updater.complete(message=response_message)

    async def cancel(
        self,
        context: agent_execution.RequestContext,
        event_queue: events.EventQueue,
    ) -> None:
        raise a2a_errors.ServerError(error=types.UnsupportedOperationError())


async def attach_a2a_routes(
    app: FastAPI,
    *,
    agent: BaseAgent,
    runner: Runner,
    task_store: TaskStore,
    rpc_path: str,
    capabilities: AgentCapabilities | None = None,
    agent_version: str | None = None,
    app_url: str | None = None,
) -> None:
    """Register A2A routes (JSON-RPC + agent-card endpoints) under ``rpc_path``."""
    if "APP_URL" not in os.environ or "0.0.0.0" in os.environ["APP_URL"]:
        os.environ["APP_URL"] = "https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app"

    resolved_app_url = app_url or os.environ["APP_URL"]
    resolved_agent_version = agent_version or os.getenv("AGENT_VERSION", "0.1.0")
    resolved_capabilities = capabilities or _default_capabilities()

    agent_card = await AgentCardBuilder(
        agent=agent,
        capabilities=resolved_capabilities,
        rpc_url=f"{resolved_app_url}{rpc_path}",
        agent_version=resolved_agent_version,
    ).build()

    from a2a.types import AgentSkill

    agent_card.description = "Intelligent procurement and inventory agent for Cymbal Coffee Roasters."
    agent_card.skills = [
        AgentSkill(
            id="check_inventory",
            name="Check Store Inventory",
            description="Monitor real-time coffee bean and milk bin telemetry levels across Cymbal Coffee store locations.",
            tags=["inventory", "telemetry"],
        ),
        AgentSkill(
            id="detect_anomalies",
            name="Detect Equipment Anomalies",
            description="Identify hopper jam anomalies, temperature spikes, and equipment maintenance issues.",
            tags=["anomalies", "equipment"],
        ),
        AgentSkill(
            id="create_purchase_order",
            name="Create Purchase Order",
            description="Automatically generate and submit Purchase Orders to suppliers when inventory drops below safety thresholds.",
            tags=["procurement", "purchase_order"],
        ),
        AgentSkill(
            id="notify_manager",
            name="Notify Store Manager",
            description="Send instant alerts to store managers regarding critical stockouts or equipment failures.",
            tags=["notifications"],
        ),
    ]

    request_handler = DefaultRequestHandler(
        agent_executor=CustomA2aAgentExecutor(agent=agent, runner=runner),
        task_store=task_store,
    )

    a2a_app = A2AFastAPIApplication(agent_card=agent_card, http_handler=request_handler)
    a2a_app.add_routes_to_app(
        app,
        agent_card_url=f"{rpc_path}{AGENT_CARD_WELL_KNOWN_PATH}",
        rpc_url=rpc_path,
        extended_agent_card_url=f"{rpc_path}{EXTENDED_AGENT_CARD_PATH}",
    )

