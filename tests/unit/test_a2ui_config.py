# Copyright 2026 Google LLC

from app.a2ui_config import (
    A2UI_VERSION,
    a2ui_system_prompt,
    extract_json_payload,
    get_a2ui_extensions,
    process_a2ui_response,
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


def test_process_a2ui_response_v09_tag():
    """Responses with <a2ui-json> tag should parse correctly."""
    text = "Here is the card:\n<a2ui-json>\n[{\"id\": \"card_1\", \"type\": \"Card\"}]\n</a2ui-json>"
    parts = process_a2ui_response(text)
    assert len(parts) == 2
    assert parts[0] == {"text": "Here is the card:"}
    assert parts[1]["metadata"]["mimeType"] == "application/json+a2ui"
    assert parts[1]["data"] == {"a2ui_messages": [{"id": "card_1", "type": "Card"}]}


def test_process_a2ui_response_raw_a2ui_messages():
    """Responses with raw a2ui_messages should extract JSON object."""
    text = "Prefix text {\"a2ui_messages\": [{\"id\": \"1\"}]}"
    parts = process_a2ui_response(text)
    assert len(parts) == 2
    assert parts[0] == {"text": "Prefix text"}
    assert parts[1]["data"] == {"a2ui_messages": [{"id": "1"}]}


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
    assert "Cymbal Coffee" in a2ui_system_prompt


def test_a2ui_version_is_set():
    """A2UI version constant should be defined."""
    assert A2UI_VERSION is not None
