# Copyright 2026 Google LLC

from app.a2ui_config import (
    A2UI_VERSION,
    a2ui_system_prompt,
    convert_v09_messages_to_v08,
    extract_json_payload,
    format_a2ui_parts,
    get_a2ui_extensions,
    normalize_a2ui_messages,
    validate_a2ui_messages,
    validate_a2ui_v08_messages,
)


def test_get_a2ui_extensions():
    """The endpoint must advertise GE v0.8 and negotiated v0.9 support."""
    extensions = get_a2ui_extensions()
    assert [extension.uri for extension in extensions] == [
        "https://a2ui.org/a2a-extension/a2ui/v0.8",
        "https://a2ui.org/a2a-extension/a2ui/v0.9",
    ]


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
    text = 'Here is the card:\n<a2ui-json>\n[{"id": "card_1", "type": "Card", "child": "text_1"}, {"id": "text_1", "type": "Text", "text": "Hello"}]\n</a2ui-json>'
    parts = format_a2ui_parts(text)
    assert len(parts) == 3
    assert parts[0].root.text == "Here is the card:"
    assert parts[1].root.metadata["mimeType"] == "application/json+a2ui"
    messages = [part.root.data for part in parts[1:]]
    validate_a2ui_messages(messages)
    assert "createSurface" in messages[0]
    assert "updateComponents" in messages[1]


def test_format_a2ui_parts_delimiter_valid_json():
    """Responses with ---a2ui_JSON--- delimiter and valid JSON should parse."""
    text = (
        'Here is the telemetry:\n---a2ui_JSON---\n```json\n'
        '[{"id": "c1", "type": "Text", "text": "Telemetry"}]\n```'
    )
    parts = format_a2ui_parts(text)
    assert len(parts) == 3
    assert parts[0].root.text == "Here is the telemetry:"
    assert parts[1].root.metadata["mimeType"] == "application/json+a2ui"
    validate_a2ui_messages([part.root.data for part in parts[1:]])


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
    """A2UI version must be v0.9."""
    assert A2UI_VERSION == "0.9"
    assert '"component":"TypeName"' in a2ui_system_prompt
    assert '"type":"TypeName"' not in a2ui_system_prompt


def test_convert_v09_messages_to_v08():
    messages = [
        {
            "version": "v0.9",
            "createSurface": {"surfaceId": "card", "catalogId": "catalog"},
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "card",
                "components": [
                    {
                        "id": "root",
                        "component": "Button",
                        "child": "label",
                        "variant": "primary",
                        "action": {
                            "event": {
                                "name": "submit",
                                "context": {"message": "Submit order"},
                            }
                        },
                    },
                    {
                        "id": "label",
                        "component": "Text",
                        "text": "Submit",
                        "variant": "body",
                    },
                ],
            },
        },
    ]

    converted = convert_v09_messages_to_v08(messages)

    assert converted[0] == {
        "beginRendering": {"surfaceId": "card", "root": "root"}
    }
    button = converted[1]["surfaceUpdate"]["components"][0]["component"]["Button"]
    assert button["primary"] is True
    assert button["action"]["context"][0]["value"] == {
        "literalString": "Submit order"
    }
    validate_a2ui_v08_messages(converted)


def test_normalize_a2ui_text_is_ascii_clean():
    messages = [
        {
            "version": "v0.9",
            "createSurface": {"surfaceId": "card", "catalogId": "catalog"},
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "card",
                "components": [
                    {
                        "id": "root",
                        "component": "Column",
                        "children": ["title", "button_text", "temperature"],
                    },
                    {
                        "id": "title",
                        "component": "Text",
                        "text": "🚨 Fleet-Wide Inventory Status",
                        "variant": "h2",
                    },
                    {
                        "id": "button_text",
                        "component": "Text",
                        "text": "?? ⚡ Expedite Reorder…",
                        "variant": "body",
                    },
                    {
                        "id": "temperature",
                        "component": "Text",
                        "text": "42.5°C — Normal",
                        "variant": "body",
                    },
                ],
            },
        },
    ]

    normalized = normalize_a2ui_messages(messages)
    values = {
        component["id"]: component["text"]
        for component in normalized[1]["updateComponents"]["components"]
        if component["component"] == "Text"
    }

    assert values == {
        "title": "Fleet-Wide Inventory Status",
        "button_text": "Expedite Reorder...",
        "temperature": "42.5 degrees C - Normal",
    }
    converted = convert_v09_messages_to_v08(normalized)
    validate_a2ui_messages(normalized)
    validate_a2ui_v08_messages(converted)


def test_convert_v09_messages_to_v08_finds_root_and_converts_media():
    messages = [
        {
            "version": "v0.9",
            "createSurface": {"surfaceId": "card", "catalogId": "catalog"},
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": "card",
                "components": [
                    {
                        "id": "image",
                        "component": "Image",
                        "url": "https://example.com/image.png",
                        "description": "Coffee beans",
                        "fit": "scaleDown",
                        "variant": "header",
                    },
                    {
                        "id": "root",
                        "component": "Column",
                        "children": ["image", "icon"],
                    },
                    {
                        "id": "icon",
                        "component": "Icon",
                        "name": "check",
                    },
                ],
            },
        },
        {
            "version": "v0.9",
            "updateDataModel": {
                "surfaceId": "card",
                "path": "/status",
                "value": "complete",
            },
        },
    ]

    converted = convert_v09_messages_to_v08(messages)

    assert converted[0]["beginRendering"]["root"] == "root"
    assert len(converted) == 2
    image = converted[1]["surfaceUpdate"]["components"][0]["component"]["Image"]
    assert image == {
        "url": {"literalString": "https://example.com/image.png"},
        "altText": {"literalString": "Coffee beans"},
        "fit": "scale-down",
        "usageHint": "header",
    }
    icon = converted[1]["surfaceUpdate"]["components"][2]["component"]["Icon"]
    assert icon["name"] == {"literalString": "check"}
    validate_a2ui_v08_messages(converted)
