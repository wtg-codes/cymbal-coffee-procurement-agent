# Copyright 2026 Google LLC

import json
import logging

from a2ui.a2a.extension import get_a2ui_agent_extension
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.constants import VERSION_0_9
from a2ui.schema.manager import A2uiSchemaManager

logger = logging.getLogger(__name__)

A2UI_VERSION = VERSION_0_9

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

UI_DESCRIPTION = """\
MANDATORY A2UI CARD GENERATION RULE:
Whenever the user asks for stock, telemetry, inventory, bin status, purchase orders, or equipment status (such as "stock downtown", "check inventory", "telemetry"), you MUST call the appropriate tool AND ALWAYS append `---a2ui_JSON---` at the end of your response followed by a valid A2UI JSON payload. You are FORBIDDEN from returning plain text alone for inventory or telemetry requests.

FORMATTING RULE:
Append `---a2ui_JSON---` at the end of your text response, followed by valid JSON containing `"a2ui_messages"`.

EXAMPLE RESPONSE FORMAT:
Here is the current inventory telemetry for the Downtown Flagship store:

---a2ui_JSON---
{
  "a2ui_messages": [
    {
      "beginRendering": { "surfaceId": "main", "root": "root_card" }
    },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          {
            "id": "root_card",
            "component": {
              "Card": { "child": "main_col" }
            }
          },
          {
            "id": "main_col",
            "component": {
              "Column": {
                "children": { "explicitList": ["header_text", "status_badge"] },
                "spacing": 8
              }
            }
          },
          {
            "id": "header_text",
            "component": {
              "Text": {
                "text": { "literalString": "Downtown Flagship Inventory Status" },
                "usageHint": "header"
              }
            }
          },
          {
            "id": "status_badge",
            "component": {
              "Text": {
                "text": { "literalString": "Status: OPTIMAL (82% Full)" }
              }
            }
          }
        ]
      }
    }
  ]
}
"""

a2ui_system_prompt = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
)


def get_a2ui_extensions():
    """Return A2UI extensions for the AgentCard capabilities."""
    return [
        get_a2ui_agent_extension(
            A2UI_VERSION,
            schema_manager.accepts_inline_catalogs,
            schema_manager.supported_catalog_ids,
        ),
    ]


def process_a2ui_response(text: str):
    """Parse model text output into A2A-compatible parts."""
    parts = []
    if "---a2ui_JSON---" in text:
        text_content, json_str = text.split("---a2ui_JSON---", 1)
        text_content = text_content.strip()
        json_str = json_str.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:]
        if json_str.endswith("```"):
            json_str = json_str[:-3]
        json_str = json_str.strip()

        if text_content:
            parts.append({"text": text_content})

        if json_str:
            try:
                data = json.loads(json_str)
                parts.append(
                    {"data": data, "metadata": {"mimeType": "application/json+a2ui"}}
                )
            except Exception as e:
                logger.error(f"Failed to parse A2UI JSON: {e}")
    else:
        parts.append({"text": text.strip()})

    return parts
