# ruff: noqa
# Copyright 2026 Google LLC

import json
import re

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.a2ui_config import a2ui_system_prompt


def _wrap_a2ui_part(a2ui_message: dict) -> types.Part:
    """Wrap a single A2UI message as a DataPart for the adk web / GE renderer."""
    datapart_json = json.dumps({
        "kind": "data",
        "metadata": {"mimeType": "application/json+a2ui"},
        "data": a2ui_message,
    })
    blob_data = (
        b"<a2a_datapart_json>"
        + datapart_json.encode("utf-8")
        + b"</a2a_datapart_json>"
    )
    return types.Part(
        inline_data=types.Blob(
            data=blob_data,
            mime_type="text/plain",
        )
    )


def a2ui_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Convert A2UI JSON in model output to rendered wire-protocol DataParts.

    The model generates a flat JSON array inside <a2ui-json> tags.
    This callback converts that to beginRendering + surfaceUpdate messages
    so that adk web and Gemini Enterprise render actual UI components.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None

    for part in llm_response.content.parts:
        if not part.text:
            continue
        text = part.text.strip()
        if not text:
            continue

        # Find the <a2ui-json> block (may have brief intro text before it)
        a2ui_match = re.search(r"<a2ui-json>(.*?)</a2ui-json>", text, re.DOTALL)
        if not a2ui_match:
            # Fall back: look for bare JSON array starting with '['
            json_start = None
            for i, ch in enumerate(text):
                if ch in ("[", "{"):
                    json_start = i
                    break
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

        if not isinstance(parsed, list):
            parsed = [parsed]

        a2ui_keys = {"beginRendering", "surfaceUpdate", "dataModelUpdate", "deleteSurface"}

        # Check if the model already output wire-protocol messages
        if any(isinstance(m, dict) and any(k in m for k in a2ui_keys) for m in parsed):
            a2ui_messages = [m for m in parsed if isinstance(m, dict) and any(k in m for k in a2ui_keys)]
        else:
            # Convert flat component array to wire protocol
            # Determine root: first component whose ID no other component references as a child
            ids = {c.get("id") for c in parsed if isinstance(c, dict)}
            referenced = set()
            for c in parsed:
                if not isinstance(c, dict):
                    continue
                if child := c.get("child"):
                    referenced.add(child)
                if children := c.get("children", {}):
                    for cid in children.get("explicitList", []):
                        referenced.add(cid)
            root_ids = ids - referenced
            root_id = next(iter(root_ids), parsed[0].get("id", "root")) if root_ids else parsed[0].get("id", "root")

            # Build surfaceUpdate component list in ADK wire format
            components = []
            for c in parsed:
                if not isinstance(c, dict):
                    continue
                comp_id = c.get("id", "unknown")
                comp_type = c.get("type", "Text")
                props = {k: v for k, v in c.items() if k not in ("id", "type")}
                components.append({"id": comp_id, "component": {comp_type: props}})

            a2ui_messages = [
                {"beginRendering": {"surfaceId": "default", "root": root_id}},
                {"surfaceUpdate": {"surfaceId": "default", "components": components}},
            ]

        new_parts = [_wrap_a2ui_part(msg) for msg in a2ui_messages]
        return LlmResponse(
            content=types.Content(role="model", parts=new_parts),
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
        model="gemini-flash-latest",
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
