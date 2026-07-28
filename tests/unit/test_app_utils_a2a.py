# Copyright 2026 Google LLC

from app.app_utils.a2a import _ADK_AGENT_EXECUTOR_EXTENSION_URI, _default_capabilities
from app.app_utils.telemetry import setup_telemetry


def test_default_capabilities():
    """Test _default_capabilities builds valid AgentCapabilities with A2UI extensions."""
    caps = _default_capabilities()
    assert caps.streaming is True
    assert len(caps.extensions) > 0
    uris = [ext.uri for ext in caps.extensions]
    assert _ADK_AGENT_EXECUTOR_EXTENSION_URI in uris


def test_setup_telemetry():
    """Test setup_telemetry executes without throwing errors."""
    setup_telemetry()


import pytest
from unittest.mock import AsyncMock, MagicMock
from app.app_utils.a2a import CustomA2aAgentExecutor


@pytest.mark.asyncio
async def test_custom_a2a_executor_execute():
    """Test CustomA2aAgentExecutor.execute extracts text and DataParts correctly."""
    agent = MagicMock()
    agent.name = "test_agent"
    runner = MagicMock()

    session_service = AsyncMock()
    session = MagicMock()
    session.id = "s1"
    session_service.get_session.return_value = session
    runner.session_service = session_service

    event1 = MagicMock()
    part_text = MagicMock(spec=["text"])
    part_text.text = "Summary text\n<a2ui-json>[\"ignored\"]</a2ui-json>"
    part_inline = MagicMock(spec=["inline_data"])
    part_inline.text = None
    part_inline.inline_data.data = b'<a2a_datapart_json>{"kind":"data","metadata":{"mimeType":"application/json+a2ui"},"data":{"beginRendering":{"surfaceId":"s1","root":"c1"}}}</a2a_datapart_json>'
    event1.content.parts = [part_text, part_inline]

    async def mock_run_async(*args, **kwargs):
        yield event1

    runner.run_async = mock_run_async

    executor = CustomA2aAgentExecutor(agent=agent, runner=runner)

    context = MagicMock()
    context.get_user_input.return_value = "Check status"
    task = MagicMock()
    task.id = "t1"
    task.context_id = "c1"
    context.current_task = task

    event_queue = AsyncMock()

    await executor.execute(context, event_queue)
    assert event_queue.enqueue_event.called
