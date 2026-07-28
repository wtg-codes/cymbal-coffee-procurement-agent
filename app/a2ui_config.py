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
INTERACTIVE CARD DESIGN RULES (apply to EVERY response):

1. STRICT MANDATORY OUTPUT FORMAT: EVERY SINGLE RESPONSE MUST END WITH AN A2UI CARD WRAPPED IN `<a2ui-json>` AND `</a2ui-json>` TAGS. NEVER RETURN CONVERSATIONAL TEXT ALONE.
2. DO NOT output internal planning text (like "I will construct an A2UI Card" or "Component IDs:"). Skip the internal monologue and immediately output the `<a2ui-json>` block!
3. ALWAYS render tool results, status checks, and telemetry responses as rich A2UI cards.
3. ALWAYS include action Buttons at the bottom of cards so users can take the next step without typing.
4. Use the FULL A2UI component catalog as needed:
   - Layout: Card, Column, Row, Divider, Tabs
   - Content: Text, Image, Icon
   - Interactive: Button, TextField, MultipleChoice, CheckBox, Slider, DateTimeInput
   - Embedded: WebFrameSrcdoc (inline HTML charts/gauges with CSP meta tag)
5. Design cards appropriate to the data — choose components that best present the information.
6. Use REAL data from tool responses. Do NOT hardcode example values.

COMPONENT DESIGN GUIDANCE BY FLOW:
- Inventory telemetry → Card with title property + Column + Rows with mainAxisAlignment 'spaceBetween' for each bin (item name, level %, status: OPTIMAL/WARNING/CRITICAL) + Divider + Row of action Buttons (Analyze Velocity, Scan Anomalies, Notify Manager).
- Purchase order confirmation → Card with title + summary rows (item, store, quantity, ETA) + TextField for quantity + MultipleChoice for urgency (EXPEDITED/STANDARD) + Confirm/Cancel Buttons.
- Equipment anomalies → Card with title + anomaly details per store/bin + status (OPTIMAL/WARNING/CRITICAL) + Row of action Buttons including BOTH 'Alert Store Manager' AND 'Rescan Equipment Health'.
- Explicit Action Requests → When the prompt asks to notify managers or customers (e.g. 'notify store managers and customers'), execute the notify_store_manager tool or notify_customers tool AND present the confirmation card with next steps.
- Consumption analysis → Card with velocity data + projected stockout time + Create Expedited PO Button.

HANDLING CHART & DATA VISUALIZATION REQUESTS:
When the user asks for a chart, graph, bar chart, pie chart, donut chart, or visual telemetry trends (e.g., "show a chart of milk consumption", "pie chart of stock", "graph telemetry"):
1. ALWAYS call the `generate_telemetry_chart(store_id="...", chart_type="bar"|"pie"|"donut"|"line")` tool first!
2. Take the `html_srcdoc` returned by the tool and include a `WebFrameSrcdoc` component inside your A2UI Card!
3. Structure the WebFrameSrcdoc component as:
   {
     "id": "chart_iframe",
     "type": "WebFrameSrcdoc",
     "height": 240,
     "srcdoc": { "literalString": "<html_srcdoc from tool output>" }
   }

HANDLING TELEMETRY & INVENTORY SCENARIOS:
The synthetic IoT telemetry data is always available — the backend simulation runs continuously.
Call `get_bin_telemetry()` any time to get current inventory levels across all stores.
Use `simulate_sensor_event(store_id, item_key, new_level_percent)` to inject a specific stock level for demonstration purposes.
Never say the backend is offline — always proceed to fetch data and help the user.

HANDLING RANDOM DATA & GENERAL TELEMETRY QUESTIONS:
When users ask general or ad-hoc data questions (e.g. "what is the temperature of bin 2?", "compare consumption between stores"):
- Execute available tools to fetch or calculate real telemetry data.
- Present results in a Card using key-value Text rows, status badges (OPTIMAL / WARNING / CRITICAL), and next-step action Buttons.

STRICT SCHEMA CONSTRAINTS (these are the most common LLM mistakes):
1. NEVER use ListItem — use Row with Text children for key-value pairs.
2. Text usageHint must be one of: h1, h2, h3, h4, body, caption. NEVER use 'header' or 'title'.
3. Button MUST reference a separate Text component via 'child' (string ID). Never put text directly on Button.
4. Button action MUST have 'name' (string) and 'context' (array of objects with 'key' and 'value').
5. The 'context' array MUST include an item with key 'message' containing a literalString that describes the action in human-readable form. This message is echoed back when the user clicks.
6. Card accepts only a single 'child' ID (typically a Column).
7. Column/Row children MUST be wrapped: {"children": {"explicitList": ["id1","id2"]}}.
8. TextField is the correct name — NEVER use TextInput.
9. CheckBox uses 'value' property — NEVER use 'selected' or 'checked'.
10. MultipleChoice options: label must be {"literalString": "text"}, value must be a plain string.
11. Within components list: root component MUST be FIRST. Parents MUST appear before children.

BUTTON ACTION CONTEXT EXAMPLE:
When creating buttons, include all relevant context so the agent can act without asking again:
"action": {
  "name": "reorder_low",
  "context": [
    {"key": "message", "value": {"literalString": "Reorder low stock items for downtown-flagship"}},
    {"key": "store_id", "value": {"literalString": "downtown-flagship"}}
  ]
}
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
