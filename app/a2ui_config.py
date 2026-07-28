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
Write a brief 1-2 sentence summary, then end every response with an A2UI card in `<a2ui-json>` and `</a2ui-json>` tags. Always include the card — never return text only.

CARD SIZE RULE: Keep cards focused and concise. For "all stores" queries, show only the most actionable data:
- Show the top 5 most critical/lowest bins across all stores (not every single bin)
- For a single store: show all bins for that store
- Always add action Buttons at the bottom of every card

CARD DESIGN BY SCENARIO:
- Inventory alerts: Card "📦 Inventory Alert" → Column of Rows for each critical/warning bin: store name, item, level%, status (CRITICAL/WARNING/OPTIMAL) → Divider → Buttons: "Analyze Velocity", "Create Purchase Order", "Scan All Anomalies"
- Single-store inventory: Card "📦 [Store Name] Inventory" → Column of all bins for that store → action Buttons
- Purchase order: Card "📋 Purchase Order Created" → summary rows (item, store, qty, cost) → MultipleChoice urgency → Confirm Button
- Equipment anomalies: Card → anomaly details → Buttons: "Alert Manager", "Rescan"
- Consumption analysis: Card → velocity, stockout projection → "Create Expedited PO" Button
- Charts: Call generate_telemetry_chart() first, put html_srcdoc in WebFrameSrcdoc (height: 240)

TOOL USAGE:
- Always call get_bin_telemetry() for inventory questions — never fabricate stock levels
- Use get_bin_telemetry(store_id="all") for fleet-wide view, get_bin_telemetry(store_id="downtown-flagship") for a single store
- Call generate_telemetry_chart() for chart/graph requests
- Call analyze_consumption_patterns() for velocity/trend questions
- Call create_purchase_order() when the user confirms a reorder
- Call detect_equipment_anomalies() for equipment/health scans
- Telemetry is always available — never say the backend is offline

SCHEMA RULES:
1. Text.usageHint: h1, h2, h3, h4, body, or caption ONLY — never "header" or "title"
2. Button: requires a "child" ID pointing to a separate Text component
3. Button.action: {"name": "action_name", "context": [{"key": "message", "value": {"literalString": "What this button does"}}, ...]}
4. Card: takes a single "child" ID — use a Column to hold multiple rows
5. Column/Row children: {"children": {"explicitList": ["id1", "id2", ...]}}
6. Component list order: root component FIRST, then parents before children
7. Never use ListItem — use Row + Text children for key-value pairs
8. Row with mainAxisAlignment "spaceBetween" for label-value pairs

BUTTON EXAMPLE:
{"id": "btn1", "type": "Button", "child": "btn1_lbl", "action": {"name": "create_po", "context": [{"key": "message", "value": {"literalString": "Create purchase order for downtown-flagship dark roast beans"}}, {"key": "store_id", "value": {"literalString": "downtown-flagship"}}, {"key": "item_key", "value": {"literalString": "dark-roast-beans"}}]}}
{"id": "btn1_lbl", "type": "Text", "text": {"literalString": "🛒 Create Purchase Order"}, "usageHint": "body"}
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
