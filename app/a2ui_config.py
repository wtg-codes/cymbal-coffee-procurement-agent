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

# --- Gauge Chart HTML Template ---
GAUGE_CHART_TEMPLATE = r"""
<meta http-equiv="Content-Security-Policy" content="connect-src 'none'">
<style>
  body{font-family:'Google Sans',sans-serif;margin:0;padding:12px;background:transparent;color:#e8eaed}
  .grid{display:flex;gap:16px;justify-content:center;flex-wrap:wrap}
  .bin{text-align:center;flex:1;min-width:100px}
  .gauge{position:relative;width:80px;height:80px;margin:0 auto 8px}
  .gauge svg{transform:rotate(-90deg)}
  .gauge circle{fill:none;stroke-width:8}
  .gauge .bg{stroke:#333}
  .gauge .fill{stroke-linecap:round;transition:stroke-dashoffset 0.5s}
  .gauge .val{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:16px;font-weight:700}
  .name{font-size:13px;font-weight:500;margin-bottom:2px}
  .detail{font-size:11px;color:#9aa0a6}
  .status{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}
  .OPTIMAL{background:#34a853}.WARNING{background:#fbbc04}.CRITICAL{background:#ea4335}
</style>
<div class="grid">BINS_HTML</div>
<script>
document.querySelectorAll('.gauge .fill').forEach(c=>{
  const r=c.r.baseVal.value,circ=2*Math.PI*r,pct=parseFloat(c.dataset.pct);
  c.style.strokeDasharray=circ;c.style.strokeDashoffset=circ-(pct/100)*circ;
});
</script>
"""

BIN_ITEM_TEMPLATE = r"""
<div class="bin">
  <div class="gauge">
    <svg viewBox="0 0 100 100"><circle class="bg" cx="50" cy="50" r="42"/><circle class="fill" cx="50" cy="50" r="42" stroke="COLOR" data-pct="PCT"/></svg>
    <div class="val">PCT%</div>
  </div>
  <div class="name">NAME</div>
  <div class="detail">WEIGHT kg / CAP kg</div>
  <div class="detail"><span class="status STATUS"></span>STATUS · RATE kg/hr</div>
</div>
"""

# --- UI Description (10x Redesign) ---
UI_DESCRIPTION = """\
MANDATORY A2UI CARD GENERATION RULE:
Whenever the user asks for stock, telemetry, inventory, bin status, purchase orders, equipment status, \
consumption, or velocity (such as "stock downtown", "check inventory", "telemetry", "purchase order", \
"detect anomalies", "consumption patterns"), you MUST call the appropriate tool AND ALWAYS append \
`---a2ui_JSON---` at the end of your response followed by a valid A2UI JSON payload.
You are FORBIDDEN from returning plain text alone for these requests.

STRICT SCHEMA CONSTRAINTS (DO NOT VIOLATE):
1. Allowed Components ONLY: 'Card', 'Column', 'Row', 'Text', 'Divider', 'Button', 'TextField', 'MultipleChoice', 'WebFrameSrcdoc'.
2. NEVER use 'ListItem' as a component name! 'ListItem' is INVALID. Use 'Row' with 'Text' children for key-value pairs.
3. Allowed usageHint values for Text components ONLY: 'h1', 'h2', 'h3', 'body', 'caption'. NEVER use 'header' or 'title'!
4. Button components MUST reference a separate Text component via 'child' (string ID). NEVER put text directly on Button.
5. Button 'action' MUST include 'name' and 'context' array. Each context item has 'key' and 'value' (with 'literalString' or 'path').
6. The 'context' array MUST include an item with key 'message' containing a human-readable description of the action.

INTERACTIVE CARD DESIGN RULES:
- ALWAYS include action buttons at the bottom of inventory/telemetry cards so users can take immediate action.
- For inventory cards: include buttons for "Reorder Low Items", "Run Anomaly Scan", "Analyze Velocity", "Notify Manager".
- For PO creation: FIRST show a confirmation card with order details, TextField for quantity, MultipleChoice for urgency, and Confirm/Cancel buttons.
- For anomaly reports: include buttons for "Alert Manager" and "Rescan".
- Group buttons in Row components with distribution "spaceAround".

EXAMPLE — INVENTORY DASHBOARD WITH GAUGES AND BUTTONS:
Here is the inventory telemetry for Downtown Flagship:

---a2ui_JSON---
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "root_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "root_card", "component": { "Card": { "child": "main_col" } } },
          { "id": "main_col", "component": { "Column": { "children": { "explicitList": ["header_text", "ts_text", "div1", "gauge_frame", "div2", "btn_row1", "btn_row2"] }, "spacing": 12 } } },
          { "id": "header_text", "component": { "Text": { "text": { "literalString": "Downtown Flagship — Inventory Status" }, "usageHint": "h2" } } },
          { "id": "ts_text", "component": { "Text": { "text": { "literalString": "Last Updated: 2026-07-27 17:59" }, "usageHint": "caption" } } },
          { "id": "div1", "component": { "Divider": { "axis": "horizontal" } } },
          { "id": "gauge_frame", "component": { "WebFrameSrcdoc": { "srcdoc": { "literalString": "GAUGE_HTML_HERE" }, "height": 180 } } },
          { "id": "div2", "component": { "Divider": { "axis": "horizontal" } } },
          { "id": "btn_row1", "component": { "Row": { "children": { "explicitList": ["btn_reorder", "btn_anomaly"] }, "distribution": "spaceAround" } } },
          { "id": "btn_row2", "component": { "Row": { "children": { "explicitList": ["btn_velocity", "btn_notify"] }, "distribution": "spaceAround" } } },
          { "id": "btn_reorder", "component": { "Button": { "child": "btn_reorder_t", "action": { "name": "reorder_low", "context": [{ "key": "message", "value": { "literalString": "Reorder low stock items for downtown-flagship" } }, { "key": "store_id", "value": { "literalString": "downtown-flagship" } }] } } } },
          { "id": "btn_reorder_t", "component": { "Text": { "text": { "literalString": "🛒 Reorder Low Items" } } } },
          { "id": "btn_anomaly", "component": { "Button": { "child": "btn_anomaly_t", "action": { "name": "run_anomaly_scan", "context": [{ "key": "message", "value": { "literalString": "Run equipment anomaly scan for downtown-flagship" } }, { "key": "store_id", "value": { "literalString": "downtown-flagship" } }] } } } },
          { "id": "btn_anomaly_t", "component": { "Text": { "text": { "literalString": "🔍 Run Anomaly Scan" } } } },
          { "id": "btn_velocity", "component": { "Button": { "child": "btn_velocity_t", "action": { "name": "analyze_velocity", "context": [{ "key": "message", "value": { "literalString": "Analyze consumption velocity for downtown-flagship" } }, { "key": "store_id", "value": { "literalString": "downtown-flagship" } }] } } } },
          { "id": "btn_velocity_t", "component": { "Text": { "text": { "literalString": "📊 Analyze Velocity" } } } },
          { "id": "btn_notify", "component": { "Button": { "child": "btn_notify_t", "action": { "name": "notify_manager", "context": [{ "key": "message", "value": { "literalString": "Notify store manager for downtown-flagship" } }, { "key": "store_id", "value": { "literalString": "downtown-flagship" } }] } } } },
          { "id": "btn_notify_t", "component": { "Text": { "text": { "literalString": "📢 Notify Manager" } } } }
        ]
      }
    }
  ]
}

EXAMPLE — PO CONFIRMATION WITH FORM INPUTS:
When creating a purchase order, FIRST show a confirmation card BEFORE executing the order:

---a2ui_JSON---
{
  "a2ui_messages": [
    { "beginRendering": { "surfaceId": "main", "root": "po_card" } },
    {
      "surfaceUpdate": {
        "surfaceId": "main",
        "components": [
          { "id": "po_card", "component": { "Card": { "child": "po_col" } } },
          { "id": "po_col", "component": { "Column": { "children": { "explicitList": ["po_title", "div_a", "item_row", "store_row", "stock_row", "eta_row", "div_b", "qty_field", "urgency_select", "div_c", "confirm_row"] }, "spacing": 10 } } },
          { "id": "po_title", "component": { "Text": { "text": { "literalString": "⚠️ Confirm Purchase Order" }, "usageHint": "h2" } } },
          { "id": "div_a", "component": { "Divider": { "axis": "horizontal" } } },
          { "id": "item_row", "component": { "Row": { "children": { "explicitList": ["item_lbl", "item_val"] } } } },
          { "id": "item_lbl", "component": { "Text": { "text": { "literalString": "Item:" }, "usageHint": "body" } } },
          { "id": "item_val", "component": { "Text": { "text": { "literalString": "Organic Dark Roast Beans" }, "usageHint": "body" } } },
          { "id": "store_row", "component": { "Row": { "children": { "explicitList": ["store_lbl", "store_val"] } } } },
          { "id": "store_lbl", "component": { "Text": { "text": { "literalString": "Store:" }, "usageHint": "body" } } },
          { "id": "store_val", "component": { "Text": { "text": { "literalString": "Downtown Flagship (#101)" }, "usageHint": "body" } } },
          { "id": "stock_row", "component": { "Row": { "children": { "explicitList": ["stock_lbl", "stock_val"] } } } },
          { "id": "stock_lbl", "component": { "Text": { "text": { "literalString": "Current Stock:" }, "usageHint": "body" } } },
          { "id": "stock_val", "component": { "Text": { "text": { "literalString": "3.0 kg (15%)" }, "usageHint": "body" } } },
          { "id": "eta_row", "component": { "Row": { "children": { "explicitList": ["eta_lbl", "eta_val"] } } } },
          { "id": "eta_lbl", "component": { "Text": { "text": { "literalString": "Stockout ETA:" }, "usageHint": "body" } } },
          { "id": "eta_val", "component": { "Text": { "text": { "literalString": "~2 hours" }, "usageHint": "caption" } } },
          { "id": "div_b", "component": { "Divider": { "axis": "horizontal" } } },
          { "id": "qty_field", "component": { "TextField": { "label": { "literalString": "Order Quantity (kg)" }, "text": { "path": "/order/quantity" } } } },
          { "id": "urgency_select", "component": { "MultipleChoice": { "selections": { "path": "/order/urgency" }, "options": [{ "label": { "literalString": "EXPEDITED (2hr delivery)" }, "value": "EXPEDITED" }, { "label": { "literalString": "STANDARD (24hr delivery)" }, "value": "STANDARD" }] } } },
          { "id": "div_c", "component": { "Divider": { "axis": "horizontal" } } },
          { "id": "confirm_row", "component": { "Row": { "children": { "explicitList": ["btn_confirm", "btn_cancel"] }, "distribution": "spaceAround" } } },
          { "id": "btn_confirm", "component": { "Button": { "child": "btn_confirm_t", "action": { "name": "confirm_purchase_order", "context": [{ "key": "message", "value": { "literalString": "Confirm and create purchase order" } }, { "key": "store_id", "value": { "literalString": "downtown-flagship" } }, { "key": "item_key", "value": { "literalString": "dark-roast-beans" } }, { "key": "quantity", "value": { "path": "/order/quantity" } }, { "key": "urgency", "value": { "path": "/order/urgency" } }] } } } },
          { "id": "btn_confirm_t", "component": { "Text": { "text": { "literalString": "✅ Confirm Order" } } } },
          { "id": "btn_cancel", "component": { "Button": { "child": "btn_cancel_t", "action": { "name": "cancel_order", "context": [{ "key": "message", "value": { "literalString": "Cancel purchase order" } }] } } } },
          { "id": "btn_cancel_t", "component": { "Text": { "text": { "literalString": "❌ Cancel" } } } }
        ]
      }
    }
  ]
}

IMPORTANT: For the WebFrameSrcdoc gauge chart, generate the inline HTML with SVG circular gauges. Use colors:
- Green (#34a853) for OPTIMAL status (level > 25%)
- Amber (#fbbc04) for WARNING status (15% < level <= 25%)
- Red (#ea4335) for CRITICAL status (level <= 15%)
Each gauge shows the fill percentage, item name, weight, and consumption rate.
The HTML MUST include: <meta http-equiv="Content-Security-Policy" content="connect-src 'none'">

IMPORTANT: Always use the ACTUAL data returned by the tools. Do NOT hardcode values from the examples.
Replace store names, item names, percentages, weights, and statuses with real tool output data.
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


def build_gauge_html(bins_data: list[dict]) -> str:
    """Build inline HTML gauge chart from bin telemetry data."""
    bins_html = ""
    for b in bins_data:
        pct = b.get("level_percent", 0)
        status = b.get("status", "OPTIMAL")
        color = "#34a853" if status == "OPTIMAL" else "#fbbc04" if status == "WARNING" else "#ea4335"
        item_html = BIN_ITEM_TEMPLATE
        item_html = item_html.replace("COLOR", color)
        item_html = item_html.replace("PCT", str(round(pct)))
        item_html = item_html.replace("NAME", b.get("item_name", "Unknown"))
        item_html = item_html.replace("WEIGHT", str(b.get("current_weight_kg", 0)))
        item_html = item_html.replace("CAP", str(b.get("max_capacity_kg", 20)))
        item_html = item_html.replace("STATUS", status)
        item_html = item_html.replace("RATE", str(b.get("hourly_consumption_kg", 0)))
        bins_html += item_html

    return GAUGE_CHART_TEMPLATE.replace("BINS_HTML", bins_html)


def extract_json_payload(json_str: str) -> dict | None:
    """Robustly extract and parse JSON payload even with surrounding markdown or comments."""
    if not json_str:
        return None
    clean = json_str.strip()
    if clean.startswith("```json"):
        clean = clean[7:]
    if clean.startswith("```"):
        clean = clean[3:]
    if clean.endswith("```"):
        clean = clean[:-3]
    clean = clean.strip()

    start_idx = clean.find("{")
    end_idx = clean.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = clean[start_idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    try:
        return json.loads(clean)
    except Exception as e:
        logger.error(f"Failed to parse A2UI JSON: {e}")
        return None


def process_a2ui_response(text: str):
    """Parse model text output into A2A-compatible parts."""
    parts = []
    if "---a2ui_JSON---" in text:
        text_content, json_str = text.split("---a2ui_JSON---", 1)
        text_content = text_content.strip()

        if text_content:
            parts.append({"text": text_content})

        data = extract_json_payload(json_str)
        if data:
            parts.append(
                {"data": data, "metadata": {"mimeType": "application/json+a2ui"}}
            )
    else:
        parts.append({"text": text.strip()})

    return parts
