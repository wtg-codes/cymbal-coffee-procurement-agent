# Copyright 2026 Google LLC

from unittest.mock import AsyncMock, MagicMock

import pytest
from a2a import types

from app.app_utils.a2a import (
    _A2UI_V08_EXTENSION_URI,
    _ADK_AGENT_EXECUTOR_EXTENSION_URI,
    CustomA2aAgentExecutor,
    _activate_a2ui_version,
    _default_capabilities,
    _has_complete_a2ui_surface,
    _scope_a2ui_surface_ids,
)
from app.app_utils.telemetry import setup_telemetry


def test_default_capabilities():
    """Test _default_capabilities builds valid AgentCapabilities with A2UI extensions."""
    caps = _default_capabilities()
    assert caps.streaming is False
    assert len(caps.extensions) > 0
    uris = [ext.uri for ext in caps.extensions]
    assert _ADK_AGENT_EXECUTOR_EXTENSION_URI in uris
    assert uris.count(_A2UI_V08_EXTENSION_URI) == 1
    assert uris.count("https://a2ui.org/a2a-extension/a2ui/v0.9") == 1
    a2ui_extension = next(ext for ext in caps.extensions if "a2ui/v0.9" in ext.uri)
    assert a2ui_extension.params == {
        "supportedCatalogIds": [
            "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"
        ]
    }


def test_setup_telemetry():
    """Test setup_telemetry executes without throwing errors."""
    setup_telemetry()


def test_has_complete_a2ui_surface_requires_create_and_update():
    create = types.Part(
        root=types.DataPart(data={"version": "v0.9", "createSurface": {}})
    )
    update = types.Part(
        root=types.DataPart(data={"version": "v0.9", "updateComponents": {}})
    )

    assert not _has_complete_a2ui_surface([])
    assert not _has_complete_a2ui_surface([create])
    assert _has_complete_a2ui_surface([create, update])


def test_activate_a2ui_version_defaults_to_ge_v08():
    context = MagicMock()
    context.requested_extensions = set()
    context.message = None
    agent_card = MagicMock()
    agent_card.capabilities.extensions = [
        types.AgentExtension(uri=_A2UI_V08_EXTENSION_URI),
        types.AgentExtension(
            uri="https://a2ui.org/a2a-extension/a2ui/v0.9"
        ),
    ]

    assert _activate_a2ui_version(context, agent_card) == "0.8"
    context.add_activated_extension.assert_called_once_with(
        _A2UI_V08_EXTENSION_URI
    )


def test_scope_a2ui_surface_ids_uses_same_task_suffix():
    messages = [
        {
            "version": "v0.9",
            "createSurface": {"surfaceId": "cardSurface", "catalogId": "catalog"},
        },
        {
            "version": "v0.9",
            "updateComponents": {"surfaceId": "cardSurface", "components": []},
        },
    ]

    _scope_a2ui_surface_ids(messages, "task-1234")

    assert messages[0]["createSurface"]["surfaceId"] == "cardSurface-task1234"
    assert (
        messages[1]["updateComponents"]["surfaceId"]
        == messages[0]["createSurface"]["surfaceId"]
    )


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

    agent_card = MagicMock()
    agent_card.capabilities.extensions = [
        types.AgentExtension(
            uri="https://a2ui.org/a2a-extension/a2ui/v0.9",
        )
    ]
    executor = CustomA2aAgentExecutor(
        agent=agent,
        runner=runner,
        agent_card=agent_card,
    )

    context = MagicMock()
    context.get_user_input.return_value = "Check status"
    context.requested_extensions = {
        "https://a2ui.org/a2a-extension/a2ui/v0.9",
    }
    task = MagicMock()
    task.id = "t1"
    task.context_id = "c1"
    context.current_task = task

    event_queue = AsyncMock()

    await executor.execute(context, event_queue)
    assert event_queue.enqueue_event.called
    context.add_activated_extension.assert_called_once_with(
        "https://a2ui.org/a2a-extension/a2ui/v0.9"
    )
    final_event = event_queue.enqueue_event.call_args_list[-1].args[0]
    final_parts = final_event.status.message.parts
    final_data = [
        part.root.data
        for part in final_parts
        if isinstance(part.root, types.DataPart)
    ]
    assert len(final_data) == 2
    assert "createSurface" in final_data[0]
    assert "updateComponents" in final_data[1]
    assert (
        final_data[0]["createSurface"]["surfaceId"]
        == final_data[1]["updateComponents"]["surfaceId"]
        == "fleet_inventory-t1"
    )
