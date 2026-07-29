# Copyright 2026 Google LLC

import json
import logging
import re
import unicodedata
from typing import Any

from a2a import types
from a2ui.a2a.extension import get_a2ui_agent_extension
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.constants import VERSION_0_8, VERSION_0_9
from a2ui.schema.manager import A2uiSchemaManager
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

logger = logging.getLogger(__name__)

A2UI_VERSION = VERSION_0_9

schema_manager = A2uiSchemaManager(
    version=A2UI_VERSION,
    catalogs=[
        BasicCatalog.get_config(version=A2UI_VERSION),
    ],
)
A2UI_CATALOG_ID = schema_manager.supported_catalog_ids[0]
v08_schema_manager = A2uiSchemaManager(
    version=VERSION_0_8,
    catalogs=[
        BasicCatalog.get_config(version=VERSION_0_8),
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
UI_DESCRIPTION = f"""\
RESPONSE FORMAT:
Write a brief 1-2 sentence summary, then output A2UI wire-protocol JSON inside <a2ui-json> and </a2ui-json> tags.
ALWAYS output an A2UI card for every response (inventory, analysis, PO confirmation, diagnostics, chart requests). Max 15 components.

OUTPUT: A JSON array with TWO messages: first createSurface, then updateComponents.
Every message MUST include "version":"v0.9". The createSurface message MUST use catalogId "{A2UI_CATALOG_ID}".
The updateComponents list uses flat components: {{"id":"...", "component":"TypeName", ...props}}.
The FIRST component MUST have id "root".

ALLOWED A2UI 0.9 COMPONENTS ONLY (Other components like WebFrameSrcdoc cause Form Validation Error):
Card:    props = {{"child": "<component_id>"}}            ← ONLY 'child'. NO title/label/header.
Column:  props = {{"children": ["id1","id2"], "justify": "start"|"spaceBetween"|"spaceAround"|"spaceEvenly"|"center"|"end"|"stretch", "align": "start"|"center"|"end"|"stretch"}}
Row:     props = same as Column
Text:    props = {{"text": "...", "variant": "h1"|"h2"|"h3"|"h4"|"h5"|"body"|"caption"}}
Button:  props = {{"child": "<label_id>", "variant": "primary"|"default"|"borderless", "action": {{"event":{{"name":"action_name", "context":{{"message":"..."}}}}}}}}
Divider: props = {{"axis": "horizontal"|"vertical"}}

STRICT RULES TO PREVENT FORM VALIDATION ERRORS:
1. Card has ONLY "child" — no other properties.
2. Use "justify" and "align" on Row/Column — NOT "distribution", "alignment", or "mainAxisAlignment".
3. Text variant ONLY: h1 h2 h3 h4 h5 body caption.
4. No emoji — ASCII text only.
5. Every ID in "child" / "children" MUST exist as a component in the same updateComponents.
6. Put card titles as Text h2 components inside the Column.
7. FORBIDDEN: WebFrameSrcdoc, WebFrameUrl, or custom component names.
8. Do NOT use beginRendering, surfaceUpdate, type, explicitList, usageHint, primary, or literalString.

CHARTS & VISUAL TELEMETRY:
- For chart/graph requests: render a visual A2UI card with progress bar Image components (e.g. url="/api/progress-bar?percent=6.2&status=critical"), stock status badges (CRITICAL/WARNING/HEALTHY), and formatted metric rows.
- STRICT CATALOG REQUIREMENT: You MUST ONLY use valid A2UI 0.9 components: Card, Column, Row, Text, Button, Divider, Image, Icon.
- NEVER use WebFrameSrcdoc or WebFrameUrl — they are unsupported extensions in v0.9 and cause form validation errors.

Structure of <a2ui-json> block:
<a2ui-json>
[
  {{"version":"v0.9", "createSurface":{{"surfaceId":"cardSurface", "catalogId":"{A2UI_CATALOG_ID}"}}}},
  {{"version":"v0.9", "updateComponents":{{"surfaceId":"cardSurface", "components":[
      {{"id":"root",    "component":"Card",   "child":"col"}},
      {{"id":"col",     "component":"Column", "children":["title","divider","row1","btn"], "justify":"start", "align":"stretch"}},
      {{"id":"title",   "component":"Text",   "text":"Fleet Inventory Telemetry", "variant":"h2"}},
      {{"id":"divider", "component":"Divider","axis":"horizontal"}},
      {{"id":"row1",    "component":"Row",    "children":["lbl1","img1","val1"], "justify":"spaceBetween"}},
      {{"id":"lbl1",    "component":"Text",   "text":"Barista Oat Milk", "variant":"body"}},
      {{"id":"img1",    "component":"Image",  "url":"/api/progress-bar?percent=6.2&status=critical", "description":"6.2% Critical", "fit":"contain"}},
      {{"id":"val1",    "component":"Text",   "text":"6.2% CRITICAL", "variant":"body"}},
      {{"id":"btn",     "component":"Button", "child":"btnText", "variant":"primary", "action":{{"event":{{"name":"reorder", "context":{{"message":"Reorder Oat Milk"}}}}}}}},
      {{"id":"btnText", "component":"Text",   "text":"Reorder Oat Milk", "variant":"body"}}
  ]}}}}
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
    """Return the A2UI versions supported by the A2A endpoint."""
    return [
        get_a2ui_agent_extension(
            VERSION_0_8,
            v08_schema_manager.accepts_inline_catalogs,
            v08_schema_manager.supported_catalog_ids,
        ),
        get_a2ui_agent_extension(
            A2UI_VERSION,
            schema_manager.accepts_inline_catalogs,
            schema_manager.supported_catalog_ids,
        ),
    ]


def _schema_validator(
    manager: A2uiSchemaManager = schema_manager,
) -> Draft202012Validator:
    """Build a validator from the exact schemas loaded by an A2UI SDK manager."""
    catalog = manager.get_selected_catalog()
    catalog_alias = (
        catalog.s2c_schema["$id"].rsplit("/", 1)[0] + "/catalog.json"
    )
    registry = Registry()
    for uri, schema in (
        (catalog.common_types_schema["$id"], catalog.common_types_schema),
        (catalog.catalog_schema["$id"], catalog.catalog_schema),
        (catalog_alias, catalog.catalog_schema),
    ):
        registry = registry.with_resource(uri, Resource.from_contents(schema))
    return Draft202012Validator(catalog.s2c_schema, registry=registry)


def validate_a2ui_message(message: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError when a message is not valid A2UI v0.9."""
    _schema_validator().validate(message)


def validate_a2ui_messages(messages: list[dict[str, Any]]) -> None:
    """Validate every A2UI v0.9 wire message in order."""
    validator = _schema_validator()
    for message in messages:
        validator.validate(message)


def validate_a2ui_v08_messages(messages: list[dict[str, Any]]) -> None:
    """Validate every A2UI v0.8 wire message in order."""
    v08_schema_manager.get_selected_catalog().validator.validate(messages)


def _literal_value(value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    for key in ("literalString", "literalNumber", "literalBoolean"):
        if key in value:
            return value[key]
    return value


def _ascii_text(value: Any) -> Any:
    """Return renderer-safe ASCII for visible A2UI text."""
    if not isinstance(value, str):
        return value
    replacements = str.maketrans(
        {
            "\u2013": "-",
            "\u2014": "-",
            "\u2018": "'",
            "\u2019": "'",
            "\u201c": '"',
            "\u201d": '"',
            "\u2026": "...",
            "\u00b0": " degrees ",
        }
    )
    ascii_value = (
        unicodedata.normalize("NFKD", value.translate(replacements))
        .encode("ascii", errors="ignore")
        .decode("ascii")
    )
    ascii_value = re.sub(r"^\s*(?:\?{2,}\s*)+", "", ascii_value)
    return re.sub(r"[^\S\n]+", " ", ascii_value).strip()


def _normalize_action(action: Any) -> Any:
    if not isinstance(action, dict) or "event" in action or "functionCall" in action:
        return action
    context = action.get("context", {})
    if isinstance(context, list):
        context = {
            item["key"]: _literal_value(item.get("value"))
            for item in context
            if isinstance(item, dict) and "key" in item
        }
    return {
        "event": {
            "name": action.get("name", "action"),
            "context": context,
        }
    }


def normalize_a2ui_component(component: dict[str, Any]) -> dict[str, Any]:
    """Convert v0.8 or early flat component syntax to canonical A2UI v0.9."""
    component_id = component.get("id")
    raw_component = component.get("component")

    if isinstance(raw_component, dict) and raw_component:
        component_type, raw_props = next(iter(raw_component.items()))
        props = dict(raw_props) if isinstance(raw_props, dict) else {}
    else:
        component_type = raw_component or component.get("type") or "Text"
        props = {
            key: value
            for key, value in component.items()
            if key not in {"id", "type", "component"}
        }

    if isinstance(props.get("children"), dict) and "explicitList" in props["children"]:
        props["children"] = props["children"]["explicitList"]
    if "distribution" in props:
        props["justify"] = props.pop("distribution")
    if "alignment" in props:
        props["align"] = props.pop("alignment")
    if "usageHint" in props:
        props["variant"] = props.pop("usageHint")
    if "primary" in props:
        props["variant"] = "primary" if props.pop("primary") else "default"
    if "text" in props:
        props["text"] = _ascii_text(_literal_value(props["text"]))
    if "url" in props:
        props["url"] = _literal_value(props["url"])
    if "altText" in props and "description" not in props:
        props["description"] = props.pop("altText")
    if "description" in props:
        props["description"] = _ascii_text(_literal_value(props["description"]))
    if "action" in props:
        props["action"] = _normalize_action(props["action"])

    return {"id": component_id, "component": component_type, **props}


def build_v09_surface(
    surface_id: str,
    components: list[dict[str, Any]],
    root_id: str | None = None,
) -> list[dict[str, Any]]:
    """Build canonical createSurface/updateComponents messages."""
    normalized = [normalize_a2ui_component(component) for component in components]
    selected_root = root_id or (normalized[0].get("id") if normalized else None)
    if selected_root != "root":
        normalized.insert(
            0,
            {
                "id": "root",
                "component": "Column",
                "children": [selected_root] if selected_root else [],
            },
        )

    return [
        {
            "version": "v0.9",
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": A2UI_CATALOG_ID,
            },
        },
        {
            "version": "v0.9",
            "updateComponents": {
                "surfaceId": surface_id,
                "components": normalized,
            },
        },
    ]


def normalize_a2ui_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize complete legacy or current wire messages to A2UI v0.9."""
    if messages and all(
        message.get("version") == "v0.9"
        and any(key in message for key in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface"))
        for message in messages
    ):
        normalized_messages = []
        for message in messages:
            update = message.get("updateComponents")
            if isinstance(update, dict):
                message = {
                    **message,
                    "updateComponents": {
                        **update,
                        "components": [
                            normalize_a2ui_component(component)
                            for component in update.get("components", [])
                        ],
                    },
                }
            normalized_messages.append(message)
        return sorted(
            normalized_messages,
            key=lambda message: "createSurface" not in message,
        )

    surface_id = "main"
    root_id = None
    components: list[dict[str, Any]] = []
    for message in messages:
        if "beginRendering" in message:
            begin = message["beginRendering"]
            surface_id = begin.get("surfaceId", surface_id)
            root_id = begin.get("root", root_id)
        if "surfaceUpdate" in message:
            update = message["surfaceUpdate"]
            surface_id = update.get("surfaceId", surface_id)
            components = update.get("components", components)

    if components:
        return build_v09_surface(surface_id, components, root_id)
    return messages


def _v08_dynamic_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value
    if isinstance(value, bool):
        return {"literalBoolean": value}
    if isinstance(value, (int, float)):
        return {"literalNumber": value}
    return {"literalString": str(value)}


def _v08_action(action: Any) -> Any:
    if not isinstance(action, dict) or "event" not in action:
        return action
    event = action["event"]
    context = event.get("context", {})
    return {
        "name": event.get("name", "action"),
        "context": [
            {"key": key, "value": _v08_dynamic_value(value)}
            for key, value in context.items()
        ],
    }


def _v08_component(component: dict[str, Any]) -> dict[str, Any]:
    component_type = component["component"]
    props = {
        key: value
        for key, value in component.items()
        if key not in {"id", "component"}
    }

    if isinstance(props.get("children"), list):
        props["children"] = {"explicitList": props["children"]}
    if "justify" in props:
        props["distribution"] = props.pop("justify")
    if "align" in props:
        props["alignment"] = props.pop("align")
    if component_type == "Text":
        if "text" in props:
            props["text"] = _v08_dynamic_value(props["text"])
        if "variant" in props:
            props["usageHint"] = props.pop("variant")
    elif component_type == "Image":
        if "url" in props:
            props["url"] = _v08_dynamic_value(props["url"])
        if "description" in props:
            props["altText"] = _v08_dynamic_value(props.pop("description"))
        if "variant" in props:
            props["usageHint"] = props.pop("variant")
        if props.get("fit") == "scaleDown":
            props["fit"] = "scale-down"
    elif component_type == "Icon" and "name" in props:
        props["name"] = _v08_dynamic_value(props["name"])
    elif component_type == "Button":
        if "variant" in props:
            props["primary"] = props.pop("variant") == "primary"
        if "action" in props:
            props["action"] = _v08_action(props["action"])

    return {
        "id": component["id"],
        "component": {component_type: props},
    }


def convert_v09_messages_to_v08(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert canonical v0.9 surface messages to GE-compatible A2UI v0.8."""
    roots = {}
    for message in messages:
        update = message.get("updateComponents")
        if not isinstance(update, dict):
            continue
        components = update.get("components", [])
        root = next(
            (
                component.get("id")
                for component in components
                if component.get("id") == "root"
            ),
            components[0].get("id", "root") if components else "root",
        )
        roots[update["surfaceId"]] = root
    converted: list[dict[str, Any]] = []
    for message in messages:
        if isinstance((create := message.get("createSurface")), dict):
            surface_id = create["surfaceId"]
            converted.append(
                {
                    "beginRendering": {
                        "surfaceId": surface_id,
                        "root": roots.get(surface_id, "root"),
                    }
                }
            )
        elif isinstance((update := message.get("updateComponents")), dict):
            converted.append(
                {
                    "surfaceUpdate": {
                        "surfaceId": update["surfaceId"],
                        "components": [
                            _v08_component(component)
                            for component in update.get("components", [])
                        ],
                    }
                }
            )
        elif "updateDataModel" in message:
            logger.warning(
                "Dropping v0.9 updateDataModel because it has no lossless v0.8 "
                "dataModelUpdate conversion."
            )
        elif isinstance((delete := message.get("deleteSurface")), dict):
            converted.append({"deleteSurface": delete})
    return converted


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
            if isinstance(data, dict) and "a2ui_messages" in data:
                payload_items = data["a2ui_messages"]
            else:
                payload_items = (
                    data["components"]
                    if isinstance(data, dict)
                    and isinstance(data.get("components"), list)
                    else [data]
                )

            wire_keys = {
                "beginRendering",
                "surfaceUpdate",
                "dataModelUpdate",
                "deleteSurface",
                "createSurface",
                "updateComponents",
                "updateDataModel",
            }
            if any(
                isinstance(item, dict) and wire_keys.intersection(item)
                for item in payload_items
            ):
                messages = normalize_a2ui_messages(payload_items)
            else:
                messages = build_v09_surface("main", payload_items)

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
