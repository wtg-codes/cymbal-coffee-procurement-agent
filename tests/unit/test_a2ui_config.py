# Copyright 2026 Google LLC

from app.a2ui_config import (
    A2UI_VERSION,
    a2ui_system_prompt,
    extract_json_payload,
    format_a2ui_parts,
    get_a2ui_extensions,
)


def test_get_a2ui_extensions():
    """A2UI extensions must advertise the a2ui URI on the agent card."""
    extensions = get_a2ui_extensions()
    assert len(extensions) > 0
    assert "a2ui" in extensions[0].uri


def test_extract_json_payload_variations():
    """Test extract_json_payload with markdown blocks, arrays, trailing commas, and invalid inputs."""
    assert extract_json_payload("") is None
    assert extract_json_payload("not json at all") is None

    # Array input -> wrapped in a2ui_messages
    arr_json = '```json\n[{"id": "c1", "type": "Card"}]\n```'
    parsed = extract_json_payload(arr_json)
    assert parsed == {"a2ui_messages": [{"id": "c1", "type": "Card"}]}

    # Object with trailing comma
    trailing_json = '{"a2ui_messages": [{"id": "c1",}],}'
    parsed_trailing = extract_json_payload(trailing_json)
    assert parsed_trailing is not None
    assert "a2ui_messages" in parsed_trailing

    # Balanced brace extraction
    embedded = 'Text before {"a2ui_messages": [1, 2]} text after'
    parsed_embedded = extract_json_payload(embedded)
    assert parsed_embedded == {"a2ui_messages": [1, 2]}


def test_format_a2ui_parts_v09_tag():
    """Responses with <a2ui-json> tag should parse into Text and Data parts."""
    text = 'Here is the card:\n<a2ui-json>\n[{"id": "card_1", "type": "Card"}]\n</a2ui-json>'
    parts = format_a2ui_parts(text)
    assert len(parts) == 2
    assert parts[0].root.text == "Here is the card:"
    assert parts[1].root.metadata["mimeType"] == "application/json+a2ui"
    assert "a2ui_messages" in parts[1].root.data


def test_format_a2ui_parts_delimiter_valid_json():
    """Responses with ---a2ui_JSON--- delimiter and valid JSON should parse."""
    text = (
        'Here is the telemetry:\n---a2ui_JSON---\n```json\n[{"id": "c1", "type": "Card"}]\n```'
    )
    parts = format_a2ui_parts(text)
    assert len(parts) == 2
    assert parts[0].root.text == "Here is the telemetry:"
    assert parts[1].root.metadata["mimeType"] == "application/json+a2ui"


def test_format_a2ui_parts_invalid_json():
    """Invalid JSON after delimiter should log error and return text part."""
    text = "Header text\n---a2ui_JSON---\n{invalid json"
    parts = format_a2ui_parts(text)
    assert len(parts) == 1
    assert parts[0].root.text == "Header text"


def test_format_a2ui_parts_plain_text():
    """Plain text without a2ui blocks should still return text-only part."""
    text = "Just normal text without a2ui block."
    parts = format_a2ui_parts(text)
    assert len(parts) == 1
    assert parts[0].root.text == "Just normal text without a2ui block."


def test_a2ui_system_prompt_contains_role():
    """The generated system prompt should include the role description."""
    assert "Cymbal Coffee" in a2ui_system_prompt


def test_a2ui_version_is_set():
    """A2UI version constant should be defined."""
    assert A2UI_VERSION is not None
