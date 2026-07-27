# Copyright 2026 Google LLC

from app.a2ui_config import get_a2ui_extensions, process_a2ui_response


def test_get_a2ui_extensions():
    """A2UI extensions must advertise the a2ui URI on the agent card."""
    extensions = get_a2ui_extensions()
    assert len(extensions) > 0
    assert "a2ui" in extensions[0].uri


def test_process_a2ui_response_with_a2ui_block():
    """Responses containing <a2ui-json> should parse without error."""
    text = (
        'Here is the result: <a2ui-json>[{"message":"Hi","components":[]}]</a2ui-json>'
    )
    parts = process_a2ui_response(text)
    assert parts is not None


def test_process_a2ui_response_plain_text():
    """Plain text without a2ui blocks should still return parts (text-only)."""
    text = "Just normal text without a2ui block."
    parts = process_a2ui_response(text)
    assert parts is not None


def test_a2ui_system_prompt_contains_role():
    """The generated system prompt should include the role description."""
    from app.a2ui_config import a2ui_system_prompt

    assert "Cymbal Coffee" in a2ui_system_prompt
    assert "Procurement" in a2ui_system_prompt or "procurement" in a2ui_system_prompt


def test_a2ui_version_is_set():
    """A2UI version constant should be defined."""
    from app.a2ui_config import A2UI_VERSION

    assert A2UI_VERSION is not None
