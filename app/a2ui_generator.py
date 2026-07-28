# Copyright 2026 Google LLC

"""Deterministic A2UI 0.8 Card Generator for Cymbal Coffee Procurement Agent.

Ensures 100% schema-valid, visually impressive A2UI cards are rendered for every step
of the demo scenario in Gemini Enterprise and adk web.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def build_fleet_inventory_card() -> list[dict[str, Any]]:
    """Build Fleet Critical Stock Alert Card."""
    return [
        {"beginRendering": {"surfaceId": "fleet_inventory", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "fleet_inventory",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "sub",
                                        "divider",
                                        "row1",
                                        "row2",
                                        "row3",
                                        "divider2",
                                        "btn1",
                                        "btn2",
                                    ]
                                },
                                "distribution": "start",
                                "alignment": "stretch",
                            }
                        },
                    },
                    {
                        "id": "title",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Fleet Critical Stock Alert"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "sub",
                        "component": {
                            "Text": {
                                "text": {"literalString": "4 Critical Bins Detected (<15% Capacity)"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {"id": "divider", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row1",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl1", "val1"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl1",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Downtown Flagship: Barista Oat Milk"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val1",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[==........] 6.2% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row2",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl2", "val2"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl2",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Downtown Flagship: Signature Espresso"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val2",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[====......] 14.7% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row3",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl3", "val3"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl3",
                        "component": {
                            "Text": {
                                "text": {"literalString": "SFO Terminal 2: Organic Dark Roast"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val3",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[====......] 14.1% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "btn1",
                        "component": {
                            "Button": {
                                "child": "btn1_lbl",
                                "primary": True,
                                "action": {
                                    "name": "reorder_oat",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Urgent Reorder: Downtown Oat Milk (6.2%)"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn1_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Urgent Reorder: Downtown Oat Milk (6.2%)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "btn2",
                        "component": {
                            "Button": {
                                "child": "btn2_lbl",
                                "primary": False,
                                "action": {
                                    "name": "reorder_sfo",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Reorder: SFO Organic Dark Roast (14.1%)"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn2_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Reorder: SFO Dark Roast (14.1%)"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ]


def build_po_confirmation_card(
    po_num: str = "PO-CYMBAL-8297",
    item: str = "Barista Edition Oat Milk",
    qty: str = "18.8 kg",
    cost: str = "$347.80",
    store: str = "Downtown Flagship",
    eta: str = "2 Hours (Expedited)",
) -> list[dict[str, Any]]:
    """Build Expedited Purchase Order Confirmation Card."""
    return [
        {"beginRendering": {"surfaceId": "po_confirmation", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "po_confirmation",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "sub",
                                        "divider1",
                                        "row_po",
                                        "row_store",
                                        "row_item",
                                        "row_qty",
                                        "row_cost",
                                        "row_eta",
                                        "divider2",
                                        "btn_done",
                                    ]
                                },
                                "distribution": "start",
                                "alignment": "stretch",
                            }
                        },
                    },
                    {
                        "id": "title",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Purchase Order Confirmed"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "sub",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"Expedited Order — {store}"},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_po",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_po", "val_po"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_po",
                        "component": {
                            "Text": {"text": {"literalString": "PO Number:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_po",
                        "component": {
                            "Text": {"text": {"literalString": po_num}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_store",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_store", "val_store"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_store",
                        "component": {
                            "Text": {"text": {"literalString": "Target Store:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_store",
                        "component": {
                            "Text": {"text": {"literalString": store}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_item",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_item", "val_item"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_item",
                        "component": {
                            "Text": {"text": {"literalString": "Item Ordered:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_item",
                        "component": {
                            "Text": {"text": {"literalString": item}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_qty",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_qty", "val_qty"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_qty",
                        "component": {
                            "Text": {"text": {"literalString": "Order Quantity:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_qty",
                        "component": {
                            "Text": {"text": {"literalString": qty}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_cost",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_cost", "val_cost"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_cost",
                        "component": {
                            "Text": {"text": {"literalString": "Estimated Cost:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_cost",
                        "component": {
                            "Text": {"text": {"literalString": cost}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_eta",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_eta", "val_eta"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_eta",
                        "component": {
                            "Text": {"text": {"literalString": "Delivery ETA:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_eta",
                        "component": {
                            "Text": {"text": {"literalString": eta}, "usageHint": "body"}
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "btn_done",
                        "component": {
                            "Button": {
                                "child": "btn_lbl",
                                "primary": True,
                                "action": {
                                    "name": "notify_done",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Check current bean and milk inventory telemetry for all stores"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Notify Store Manager & Return"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ]


def build_consumption_analysis_card(
    store: str = "Downtown Flagship",
    item: str = "Organic Dark Roast Beans",
    stock: str = "7.4 kg",
    rate: str = "1.2 kg/hr",
    hours: str = "6.2 Hours",
    reorder_qty: str = "40.0 kg",
) -> list[dict[str, Any]]:
    """Build Consumption Velocity & Stockout Analysis Card."""
    return [
        {"beginRendering": {"surfaceId": "consumption_analysis", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "consumption_analysis",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "sub",
                                        "divider1",
                                        "row_stock",
                                        "row_rate",
                                        "row_hours",
                                        "row_rec",
                                        "divider2",
                                        "btn_po",
                                    ]
                                },
                                "distribution": "start",
                                "alignment": "stretch",
                            }
                        },
                    },
                    {
                        "id": "title",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Consumption & Stockout Analytics"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "sub",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{store} — {item}"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_stock",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_stock", "val_stock"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_stock",
                        "component": {
                            "Text": {"text": {"literalString": "Current Stock Level:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_stock",
                        "component": {
                            "Text": {"text": {"literalString": f"{stock} [==........]"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_rate",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_rate", "val_rate"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_rate",
                        "component": {
                            "Text": {"text": {"literalString": "Hourly Burn Rate:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_rate",
                        "component": {
                            "Text": {"text": {"literalString": rate}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_hours",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_hours", "val_hours"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_hours",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Est. Time to Stockout:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_hours",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{hours} (CRITICAL)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_rec",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_rec", "val_rec"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_rec",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Recommended Reorder:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_rec",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{reorder_qty} (48-hr buffer)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "btn_po",
                        "component": {
                            "Button": {
                                "child": "btn_lbl",
                                "primary": True,
                                "action": {
                                    "name": "exec_po",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Execute expedited PO for {reorder_qty} of {item} at {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"Execute Expedited PO ({reorder_qty})"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ]


def build_equipment_diagnostic_card(
    store: str = "SFO Terminal 2",
) -> list[dict[str, Any]]:
    """Build Equipment Diagnostic Card."""
    return [
        {"beginRendering": {"surfaceId": "equipment_diagnostic", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "equipment_diagnostic",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "status",
                                        "divider1",
                                        "row_grinder",
                                        "row_chiller",
                                        "row_pump",
                                        "row_vib",
                                        "divider2",
                                        "btn_view",
                                    ]
                                },
                                "distribution": "start",
                                "alignment": "stretch",
                            }
                        },
                    },
                    {
                        "id": "title",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{store} Equipment Diagnostic"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "status",
                        "component": {
                            "Text": {
                                "text": {"literalString": "STATUS: ALL SYSTEMS HEALTHY"},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_grinder",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_g", "val_g"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_g",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Espresso Grinder Temp:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_g",
                        "component": {
                            "Text": {
                                "text": {"literalString": "42.5°C (Normal <65°C)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_chiller",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_c", "val_c"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_c",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Milk Chiller Temp:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_c",
                        "component": {
                            "Text": {
                                "text": {"literalString": "3.8°C (Normal 2-5°C)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_pump",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_p", "val_p"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_p",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Pump Pressure:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_p",
                        "component": {
                            "Text": {
                                "text": {"literalString": "9.2 Bar (Optimal)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_vib",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_v", "val_v"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_v",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Vibration Level:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_v",
                        "component": {
                            "Text": {
                                "text": {"literalString": "0.02g (Low)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "btn_view",
                        "component": {
                            "Button": {
                                "child": "btn_lbl",
                                "primary": True,
                                "action": {
                                    "name": "check_bins",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Check bin telemetry for {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"Check {store} Bin Telemetry"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ]


def build_visual_chart_card(
    store: str = "Downtown Flagship",
) -> list[dict[str, Any]]:
    """Build Visual Telemetry Bar Chart Card."""
    return [
        {"beginRendering": {"surfaceId": "visual_chart", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "visual_chart",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "sub",
                                        "divider1",
                                        "row_oat",
                                        "row_esp",
                                        "row_dark",
                                        "row_milk",
                                        "divider2",
                                        "btn_reorder",
                                    ]
                                },
                                "distribution": "start",
                                "alignment": "stretch",
                            }
                        },
                    },
                    {
                        "id": "title",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"{store} Stock Level Bar Chart"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "sub",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Real-time Telemetry Visual Comparison"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_oat",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_oat", "val_oat"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_oat",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Barista Oat Milk:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_oat",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[==........] 6.2% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_esp",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_esp", "val_esp"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_esp",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Signature Espresso:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_esp",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[====......] 14.7% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_dark",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_dark", "val_dark"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_dark",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Organic Dark Roast:"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "val_dark",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[========..] 23.0% WARNING"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_milk",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_milk", "val_milk"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_milk",
                        "component": {
                            "Text": {"text": {"literalString": "Whole Milk:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_milk",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[==========] 88.5% HEALTHY"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "btn_reorder",
                        "component": {
                            "Button": {
                                "child": "btn_lbl",
                                "primary": True,
                                "action": {
                                    "name": "reorder_critical",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Urgent Reorder: Downtown Oat Milk (6.2%)"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Reorder Critical Items"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ]


def get_scenario_card(query: str, text: str = "") -> list[dict[str, Any]]:
    """Match query intent to demo scenario card."""
    q = (query + " " + text).lower()

    if any(k in q for k in ["purchase order", "po-", "reorder", "submitted", "po confirmed", "order created"]):
        # Extract PO info if present in text
        po_match = re.search(r"PO-[A-Z0-9-]+", text)
        po_num = po_match.group(0) if po_match else "PO-CYMBAL-8297"
        item = "Barista Edition Oat Milk" if "oat" in q else "Organic Dark Roast Beans"
        qty = "40.0 kg" if "40" in q or "dark roast" in q else "18.8 kg"
        cost = "$740.00" if "40" in q or "dark roast" in q else "$347.80"
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        return build_po_confirmation_card(po_num=po_num, item=item, qty=qty, cost=cost, store=store)

    elif any(k in q for k in ["consumption", "velocity", "stockout", "burn rate"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        item = "Barista Edition Oat Milk" if "oat" in q else "Organic Dark Roast Beans"
        return build_consumption_analysis_card(store=store, item=item)

    elif any(k in q for k in ["diagnostic", "anomaly", "anomalies", "temperature", "spike", "equipment", "health"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        return build_equipment_diagnostic_card(store=store)

    elif any(k in q for k in ["chart", "graph", "bar chart", "visual"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        return build_visual_chart_card(store=store)

    else:
        # Default: Fleet Inventory Telemetry Card
        return build_fleet_inventory_card()
