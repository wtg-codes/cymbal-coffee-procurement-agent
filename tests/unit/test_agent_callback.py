# Copyright 2026 Google LLC

from google.adk.models import LlmResponse
from google.genai import types
from app.agent import a2ui_callback


def test_a2ui_callback_with_tag():
    """a2ui_callback with <a2ui-json> tag extracts text summary and A2UI DataParts."""
    resp = LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part(
                    text='Confirmation text:\n<a2ui-json>[{"id":"c1","type":"Card"}]</a2ui-json>'
                )
            ],
        )
    )
    res = a2ui_callback(None, resp)
    assert res is not None
    assert len(res.content.parts) >= 2
    assert res.content.parts[0].text == "Confirmation text:"
    assert b"<a2a_datapart_json>" in res.content.parts[1].inline_data.data


def test_a2ui_callback_without_tag_bare_json():
    """a2ui_callback without tags truncates summary before bare JSON."""
    resp = LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part(
                    text='Purchase order confirmed:{"kind":"data","metadata":{"mimeType":"application/json+a2ui"},"data":{"beginRendering":{"surfaceId":"s1","root":"c1"}}}'
                )
            ],
        )
    )
    res = a2ui_callback(None, resp)
    assert res is not None
    assert res.content.parts[0].text == "Purchase order confirmed:"
    assert "{" not in res.content.parts[0].text


def test_a2ui_callback_no_json():
    """a2ui_callback on plain text response returns None."""
    resp = LlmResponse(
        content=types.Content(
            role="model", parts=[types.Part(text="Just normal response text.")]
        )
    )
    res = a2ui_callback(None, resp)
    assert res is None
