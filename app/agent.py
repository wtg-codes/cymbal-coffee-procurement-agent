# ruff: noqa
# Copyright 2026 Google LLC

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.a2ui_config import (
    a2ui_system_prompt,
    build_v09_surface,
    normalize_a2ui_messages,
)


def _strip_non_latin1(obj):
    """Recursively replace non-Latin1 chars in string values with '?'.

    The adk web A2UI renderer calls btoa(JSON.stringify(component)) client-side.
    btoa() only accepts Latin1 (0-255). Emoji chars are above U+00FF so btoa
    throws. This strips them at the source so the renderer never sees them.
    """
    if isinstance(obj, str):
        return obj.encode("latin-1", errors="replace").decode("latin-1")
    if isinstance(obj, dict):
        return {k: _strip_non_latin1(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_strip_non_latin1(item) for item in obj]
    return obj


def _wrap_a2ui_part(a2ui_message: dict) -> types.Part:
    r"""Wrap a single A2UI wire-protocol message as a DataPart for adk web / GE.

    adk web's isA2uiDataPart() requires the inner JSON payload inside
    <a2a_datapart_json>...</a2a_datapart_json> to have:
      kind = "data"
      metadata.mimeType = "application/json+a2ui"
      data = <a2ui_message>

    Uses ensure_ascii=True so emoji/Unicode are \uXXXX-escaped, preventing
    btoa() failures in the browser renderer.
    """
    datapart_json = json.dumps(
        {
            "kind": "data",
            "metadata": {"mimeType": "application/json+a2ui"},
            "data": a2ui_message,
        },
        ensure_ascii=True,
    )
    blob_data = (
        b"<a2a_datapart_json>"
        + datapart_json.encode("ascii")
        + b"</a2a_datapart_json>"
    )
    return types.Part(
        inline_data=types.Blob(
            data=blob_data,
            mime_type="text/plain",
        )
    )


def extract_a2ui_messages(data):
    """Recursively find any wire-protocol dicts in data."""
    messages = []
    a2ui_keys = {
        "beginRendering",
        "surfaceUpdate",
        "dataModelUpdate",
        "deleteSurface",
        "createSurface",
        "updateComponents",
        "updateDataModel",
    }

    def _walk(obj):
        if isinstance(obj, dict):
            if any(k in obj for k in a2ui_keys):
                messages.append(obj)
                return
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(data)
    return messages


def a2ui_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Convert A2UI wire-protocol JSON in model output to rendered DataParts.

    The model outputs full wire-protocol JSON (beginRendering + surfaceUpdate)
    inside <a2ui-json> tags, matching the official a2ui-project samples pattern.
    This callback extracts that JSON and wraps each message as a DataPart.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None

    for part in llm_response.content.parts:
        if not part.text:
            continue
        text = part.text.strip()
        if not text:
            continue

        # Strip any literal <a2a_datapart_json> tags if present in text
        text = re.sub(r"</?a2a_datapart_json>", "", text)

        # Find the <a2ui-json> block
        a2ui_match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
        if not a2ui_match:
            # Fall back: look for bare JSON array starting with '['
            json_start = next(
                (i for i, ch in enumerate(text) if ch in ("[", "{")), None
            )
            if json_start is None:
                continue
            json_text = text[json_start:]
        else:
            json_text = a2ui_match.group(1).strip()

        # Strip markdown fences if present
        if json_text.startswith("```"):
            json_text = json_text.split("\n", 1)[-1]
            if json_text.endswith("```"):
                json_text = json_text[:-3].strip()

        # Parse the JSON
        try:
            parsed, _ = json.JSONDecoder().raw_decode(json_text)
        except json.JSONDecodeError:
            try:
                fixed = "[" + re.sub(r"\}\s*\{", "},{", json_text) + "]"
                parsed, _ = json.JSONDecoder().raw_decode(fixed)
            except json.JSONDecodeError:
                continue

        a2ui_messages = extract_a2ui_messages(parsed)

        if not a2ui_messages and isinstance(parsed, list):
            # Fallback: convert old flat component array [{"id":..., "type":..., props}]
            # to wire protocol safely.
            valid_comps = [c for c in parsed if isinstance(c, dict)]
            if not valid_comps:
                continue

            ids = {c.get("id") for c in valid_comps if isinstance(c, dict) and c.get("id")}
            referenced = set()
            for c in valid_comps:
                if not isinstance(c, dict):
                    continue
                if child := c.get("child"):
                    if isinstance(child, str):
                        referenced.add(child)
                children = c.get("children")
                if isinstance(children, dict):
                    explicit_list = children.get("explicitList")
                    if isinstance(explicit_list, list):
                        for cid in explicit_list:
                            if isinstance(cid, str):
                                referenced.add(cid)
                elif isinstance(children, list):
                    for cid in children:
                        if isinstance(cid, str):
                            referenced.add(cid)

            root_ids = [i for i in ids if i not in referenced]
            first_id = valid_comps[0].get("id") or "card"
            root_id = root_ids[0] if root_ids else first_id

            a2ui_messages = build_v09_surface(
                "default",
                valid_comps,
                root_id=root_id,
            )

        if a2ui_messages:
            a2ui_messages = normalize_a2ui_messages(a2ui_messages)

        if not a2ui_messages:
            from app.a2ui_generator import get_scenario_card
            a2ui_messages = get_scenario_card(query=text, text=text)


        # Log for debugging
        logger.info(f"--- A2UI Callback raw text:\n{text[:300]}...")
        logger.info(f"--- A2UI Callback parsed messages:\n{json.dumps(a2ui_messages, indent=2)[:500]}")

        new_parts = [_wrap_a2ui_part(_strip_non_latin1(msg)) for msg in a2ui_messages]

        # Preserve clean text summary before the A2UI JSON payload
        a2ui_match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
        if a2ui_match:
            summary_text = text.split("<a2ui-json>")[0].strip()
        else:
            json_start = next(
                (i for i, ch in enumerate(text) if ch in ("[", "{")), None
            )
            if json_start is not None:
                summary_text = text[:json_start].strip()
            else:
                summary_text = text.strip()

        summary_text = re.sub(r"</?a2a_datapart_json>", "", summary_text)
        summary_text = re.sub(r"```(?:json)?.*", "", summary_text, flags=re.DOTALL)
        summary_text = re.sub(r"\{\s*\"(?:kind|metadata|data|beginRendering|surfaceUpdate|id)\".*", "", summary_text, flags=re.DOTALL)
        summary_text = re.sub(r"\[\s*\{\s*\"(?:kind|metadata|data|beginRendering|surfaceUpdate|id)\".*", "", summary_text, flags=re.DOTALL).strip()

        if not summary_text:
            summary_text = "\u200b"  # zero-width space fallback
        text_part = types.Part(text=summary_text)

        return LlmResponse(
            content=types.Content(role="model", parts=[text_part] + new_parts),
            custom_metadata={"a2a:response": "true"},
        )

    return None
from app.tools import (
    analyze_consumption_patterns,
    create_purchase_order,
    detect_equipment_anomalies,
    generate_telemetry_chart,
    get_bin_telemetry,
    notify_store_manager,
    send_customer_notification,
    simulate_sensor_event,
)


root_agent = Agent(
    name="cymbal_coffee_procurement_agent",
    description="Intelligent procurement and inventory agent for Cymbal Coffee Roasters.",
    model=Gemini(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_system_prompt,
    tools=[
        get_bin_telemetry,
        generate_telemetry_chart,
        simulate_sensor_event,
        detect_equipment_anomalies,
        analyze_consumption_patterns,
        create_purchase_order,
        send_customer_notification,
        notify_store_manager,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
