# Copyright 2026 Google LLC

from app.a2ui_config import get_a2ui_extensions, process_a2ui_response


def test_get_a2ui_extensions():
    """A2UI extensions must advertise the a2ui URI on the agent card."""
    extensions = get_a2ui_extensions()
    assert len(extensions) > 0
    assert "a2ui" in extensions[0].uri


def test_process_a2ui_response_delimiter_valid_json():
    """Responses with ---a2ui_JSON--- delimiter and valid JSON should parse."""
    text = (
        'Here is the telemetry:\n---a2ui_JSON---\n```json\n{"a2ui_messages": []}\n```'
    )
    parts = process_a2ui_response(text)
    assert len(parts) == 2
    assert parts[0] == {"text": "Here is the telemetry:"}
    assert parts[1]["metadata"]["mimeType"] == "application/json+a2ui"
    assert parts[1]["data"] == {"a2ui_messages": []}


def test_process_a2ui_response_invalid_json():
    """Invalid JSON after delimiter should log error and fallback to text."""
    text = "Header text\n---a2ui_JSON---\n{invalid json"
    parts = process_a2ui_response(text)
    assert len(parts) == 1
    assert parts[0] == {"text": "Header text"}


def test_process_a2ui_response_plain_text():
    """Plain text without a2ui blocks should still return parts (text-only)."""
    text = "Just normal text without a2ui block."
    parts = process_a2ui_response(text)
    assert parts == [{"text": "Just normal text without a2ui block."}]


def test_a2ui_system_prompt_contains_role():
    """The generated system prompt should include the role description."""
    from app.a2ui_config import a2ui_system_prompt

    assert "Cymbal Coffee" in a2ui_system_prompt


def test_a2ui_version_is_set():
    """A2UI version constant should be defined."""
    from app.a2ui_config import A2UI_VERSION

    assert A2UI_VERSION is not None
