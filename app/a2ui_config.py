# Copyright 2026 Google LLC

import json
import logging
import re

from a2a import types
from a2ui.a2a.extension import get_a2ui_agent_extension
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.constants import VERSION_0_8
from a2ui.schema.manager import A2uiSchemaManager

logger = logging.getLogger(__name__)

A2UI_VERSION = VERSION_0_8

schema_manager = A2uiSchemaManager(
    version=A2UI_VERSION,
    catalogs=[
        BasicCatalog.get_config(version=A2UI_VERSION),
    ],
)

ROLE_DESCRIPTION = (
    "You are the Cymbal Coffee Intelligent Procurement & Inventory Agent powered by Google Cloud. "
    "Your primary function is to monitor real-time IoT telemetry from coffee bean bins and milk containers, "
    "analyze consumption velocity, detect stockout risks, automatically create Purchase Orders (POs), "
    "identify equipment anomalies, and notify store managers and customers. "
    "Always assist store managers with concise, actionable intelligence."
)

# ---------------------------------------------------------------------------
# UI_DESCRIPTION — appended AFTER the SDK's auto-injected schema + workflow
# rules. The SDK already tells the model the full component catalog and the
# <a2ui-json> tag format.  We only need to add domain-specific card design
# guidance and remind the model of strict schema pitfalls.
# ---------------------------------------------------------------------------
UI_DESCRIPTION = """\
RESPONSE FORMAT:
Write a brief 1-2 sentence summary, then output A2UI wire-protocol JSON inside <a2ui-json> and </a2ui-json> tags.
ALWAYS output an A2UI card for every response (inventory, analysis, PO confirmation, diagnostics, chart requests). Max 15 components.

OUTPUT: A JSON array with TWO messages: first a beginRendering, then a surfaceUpdate.
The surfaceUpdate components use the wrapper format: {{"id":"...", "component": {{"TypeName": <props>}}}}.

ALLOWED A2UI 0.8 COMPONENTS ONLY (Other components like WebFrameSrcdoc cause Form Validation Error):
Card:    props = {{"child": "<component_id>"}}            ← ONLY 'child'. NO title/label/header.
Column:  props = {{"children": {{"explicitList":["id1","id2"]}}, "distribution": "start"|"spaceBetween"|"spaceAround"|"center"|"end", "alignment": "start"|"center"|"end"|"stretch"}}
Row:     props = same as Column
Text:    props = {{"text": {{"literalString":"..."}}, "usageHint": "h1"|"h2"|"h3"|"h4"|"h5"|"body"|"caption"}}
Button:  props = {{"child": "<label_id>", "primary": true, "action": {{"name":"action_name", "context":[{"key":"message","value":{{"literalString":"..."}}}]}}}}
Divider: props = {{"axis": "horizontal"|"vertical"}}

STRICT RULES TO PREVENT FORM VALIDATION ERRORS:
1. Card has ONLY "child" — no other properties.
2. Use "distribution" on Row/Column — NOT "mainAxisAlignment" or "justify".
3. Text usageHint ONLY: h1 h2 h3 h4 h5 body caption.
4. No emoji — ASCII text only.
5. Every ID in "child" / "explicitList" MUST exist as a component in the same surfaceUpdate.
6. Put card titles as Text h2 components inside the Column.
7. FORBIDDEN: WebFrameSrcdoc, WebFrameUrl, or custom component names.

CHARTS & VISUAL TELEMETRY:
- For chart/graph requests: render a visual A2UI card with progress bars (e.g. "[========..] 78%"), stock status badges (CRITICAL/WARNING/HEALTHY), and formatted metric rows.
- STRICT CATALOG REQUIREMENT: You MUST ONLY use valid A2UI 0.8 components: Card, Column, Row, Text, Button, Divider, Image, Icon.
- NEVER use WebFrameSrcdoc or WebFrameUrl — they are unsupported extensions in v0.8 and cause form validation errors.

Structure of <a2ui-json> block:
<a2ui-json>
[
  {"beginRendering": {"surfaceId": "cardSurface", "root": "card"}},
  {"surfaceUpdate": {"surfaceId": "cardSurface", "components": [
      {"id":"card",    "component": {"Card":   {"child":"col"}}},
      {"id":"col",     "component": {"Column": {"children": {"explicitList":["title","divider","bar1","btn"]}}}},
      {"id":"title",   "component": {"Text":   {"text":{"literalString":"Fleet Inventory Telemetry"}, "usageHint":"h2"}}},
      {"id":"divider", "component": {"Divider":{"axis":"horizontal"}}},
      {"id":"bar1",    "component": {"Text":   {"text":{"literalString":"Oat Milk [==........] 6.2% CRITICAL"}, "usageHint":"body"}}},
      {"id":"btn",     "component": {"Button": {"child":"btnText", "primary":true, "action":{"name":"reorder", "context": [{"key":"message", "value":{"literalString":"Reorder Oat Milk"}}]}}}},
      {"id":"btnText", "component": {"Text":   {"text":{"literalString":"Reorder Oat Milk"}, "usageHint":"body"}}},
      {"id":"val1",    "component": {"Text":   {"text":{"literalString":"[========..] 23.0% OK"}, "usageHint":"body"}}}
  ]}}
]
</a2ui-json>

TOOL USAGE:
- Always call get_bin_telemetry() for inventory — never fabricate stock levels
- get_bin_telemetry(store_id="all") for fleet, get_bin_telemetry(store_id="downtown-flagship") for single store
- Call generate_telemetry_chart() for chart/graph requests
- Call analyze_consumption_patterns() for velocity/trend questions
- Call create_purchase_order() when user confirms a reorder
- Call detect_equipment_anomalies() for equipment/health scans
- Telemetry is always available — never say the backend is offline
"""


a2ui_system_prompt = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
)


def get_a2ui_extensions():
    """Return A2UI extensions for the AgentCard capabilities supporting both v0.8 and v0.9."""
    from a2a.types import AgentExtension

    return [
        AgentExtension(
            uri="https://a2ui.org/a2a-extension/a2ui/v0.8",
            description="Provides agent driven UI using the A2UI v0.8 JSON format.",
        ),
        get_a2ui_agent_extension(
            A2UI_VERSION,
            schema_manager.accepts_inline_catalogs,
            schema_manager.supported_catalog_ids,
        ),
    ]


def _fix_json_string(s: str) -> str:
    """Attempt to fix common LLM JSON mistakes."""
    # Remove trailing commas before } or ]
    s = re.sub(r",\s*([}\]])", r"\1", s)
    return s


def extract_json_payload(json_str: str) -> dict | None:
    """Robustly extract and parse JSON payload from various formats.

    Handles: {a2ui_messages: [...]}, [{...}], {root, components}, etc.
    Always returns a dict (wrapping arrays in a2ui_messages if needed).
    """
    if not json_str:
        return None
    clean = json_str.strip()

    # Strip markdown code fences
    if clean.startswith("```json"):
        clean = clean[7:]
    elif clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()

    def _try_parse(s: str):
        """Try parsing a string as JSON, with trailing comma fix fallback."""
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(_fix_json_string(s))
        except json.JSONDecodeError:
            return None

    def _normalize(parsed):
        """Normalize parsed JSON to always return a dict."""
        if isinstance(parsed, dict):
            return parsed
        if isinstance(parsed, list):
            # Wrap array in a2ui_messages — handles v0.9 array format
            return {"a2ui_messages": parsed}
        return None

    # Try parsing the whole string first (handles both objects and arrays)
    result = _try_parse(clean)
    if result is not None:
        return _normalize(result)

    # Find the outermost {...} or [...]
    first_brace = clean.find("{")
    first_bracket = clean.find("[")

    # Determine which comes first
    if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
        # Array format — find matching ]
        end_bracket = clean.rfind("]")
        if end_bracket > first_bracket:
            candidate = clean[first_bracket : end_bracket + 1]
            result = _try_parse(candidate)
            if result is not None:
                return _normalize(result)

    if first_brace != -1:
        end_brace = clean.rfind("}")
        if end_brace > first_brace:
            candidate = clean[first_brace : end_brace + 1]
            result = _try_parse(candidate)
            if result is not None:
                return _normalize(result)

        # Try balanced brace extraction
        depth = 0
        for i, ch in enumerate(clean[first_brace:], first_brace):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    balanced = clean[first_brace : i + 1]
                    result = _try_parse(balanced)
                    if result is not None:
                        return _normalize(result)
                    break

    logger.error("Failed to parse A2UI JSON. Snippet: %s", clean[:300])
    return None


def extract_a2ui_json(content: str) -> tuple[str, list[str]]:
    """Extract human text and A2UI JSON strings from LLM output."""
    if not content:
        return "", []

    text_part = content
    json_blocks = []

    if "<a2ui-json>" in content and "</a2ui-json>" in content:
        parts = []
        curr = content
        while "<a2ui-json>" in curr and "</a2ui-json>" in curr:
            start = curr.find("<a2ui-json>")
            end = curr.find("</a2ui-json>")
            parts.append(curr[:start])
            json_blocks.append(curr[start + len("<a2ui-json>") : end].strip())
            curr = curr[end + len("</a2ui-json>") :]
        parts.append(curr)
        text_part = "".join(parts).strip()
    elif "---a2ui_JSON---" in content:
        splits = content.split("---a2ui_JSON---", 1)
        text_part = splits[0].strip()
        json_blocks.append(splits[1].strip())

    return text_part, json_blocks


def format_a2ui_parts(final_response_content: str) -> list[types.Part]:
    """Format final text and extracted A2UI JSON into A2A Part objects.

    Produces TextPart and DataParts with mimeType 'application/json+a2ui'.
    """
    clean_text, json_blocks = extract_a2ui_json(final_response_content)

    parts: list[types.Part] = []

    if clean_text:
        parts.append(types.Part(root=types.TextPart(text=clean_text)))

    for json_str in json_blocks:
        data = extract_json_payload(json_str)
        if data:
            messages = []
            if isinstance(data, dict) and "a2ui_messages" in data:
                messages = data["a2ui_messages"]
            else:
                # Extract flat components list
                components = []
                if isinstance(data, list):
                    components = data
                elif isinstance(data, dict):
                    if "components" in data and isinstance(data["components"], list):
                        components = data["components"]
                    else:
                        components = [data]

                messages = [
                    {"beginRendering": {"surfaceId": "main"}},
                    {"surfaceUpdate": {"surfaceId": "main", "components": components}},
                ]

            # Ensure beginRendering is first
            begin_idx = -1
            for i, msg in enumerate(messages):
                if "beginRendering" in msg:
                    begin_idx = i
                    break

            if begin_idx > 0:
                msg = messages.pop(begin_idx)
                messages.insert(0, msg)

            for msg in messages:
                parts.append(
                    types.Part(
                        root=types.DataPart(
                            data=msg,
                            metadata={"mimeType": "application/json+a2ui"},
                        )
                    )
                )

    if not parts:
        parts.append(types.Part(root=types.TextPart(text=final_response_content)))

    return parts


process_a2ui_response = format_a2ui_parts
