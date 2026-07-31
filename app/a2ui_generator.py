# Copyright 2026 Google LLC

"""Deterministic A2UI v0.9 Card Generator for Cymbal Coffee Procurement Agent.

Ensures 100% schema-valid, visually impressive A2UI cards are rendered for every step
of the demo scenario in Gemini Enterprise and adk web.

Demo flow (linear, no circular PO loops):
  Card 1 (Fleet Alert) -> Card 2 (PO Confirmed) -> Card 5 (Delivery Tracking)
                       \\-> Card 3 (Consumption)  -> Card 2 (PO Confirmed)
                                                         \\-> Card 4 (Manager Notified)
  Card 6 (Equipment) -> Card 4 (Manager Notified) -> Card 1 (Fleet Alert)
"""

import logging
import os
import re
from typing import Any
from urllib.parse import urlencode

from app.a2ui_config import normalize_a2ui_messages

logger = logging.getLogger(__name__)


def _get_base_url() -> str:
    """Return the absolute app URL for building Image src attributes.

    Reads APP_URL from the environment (set by Terraform / Cloud Run).
    Falls back to empty string for local dev (images will use relative URLs).
    """
    url = os.getenv("APP_URL", "").strip().rstrip("/")
    if url and "0.0.0.0" not in url:
        return url
    return ""


def _progress_bar_url(percent: float, status: str) -> str:
    """Build an absolute URL for the SVG progress bar endpoint."""
    base = _get_base_url()
    params = urlencode({"percent": percent, "status": status})
    return f"{base}/api/progress-bar?{params}"


def _progress_image(component_id: str, percent: float, status: str) -> dict:
    """Build an A2UI Image component for an SVG progress bar."""
    return {
        "id": component_id,
        "component": {
            "Image": {
                "url": {"literalString": _progress_bar_url(percent, status)},
                "altText": {"literalString": f"{percent}% {status.title()}"},
                "fit": "contain",
            }
        },
    }


def build_fleet_inventory_card() -> list[dict[str, Any]]:
    """Build Fleet Critical Stock Alert Card (Card 1 — Demo Entry Point).

    Buttons flow FORWARD:
      - "Emergency Reorder: Oat Milk" -> PO Confirmed card (Card 2)
      - "View Consumption Analysis" -> Consumption card (Card 3)
    """
    return normalize_a2ui_messages([
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
                                        "btn_reorder",
                                        "btn_analysis",
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
                                "text": {"literalString": "3 Critical Bins Detected (< 15% Capacity) across 2 stores"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {"id": "divider", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row1",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl1", "img1", "val1"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl1",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Downtown: Barista Oat Milk"},
                                "usageHint": "body",
                            }
                        },
                    },
                    _progress_image("img1", 6.2, "critical"),
                    {
                        "id": "val1",
                        "component": {
                            "Text": {
                                "text": {"literalString": "6.2% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row2",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl2", "img2", "val2"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl2",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Downtown: Signature Espresso"},
                                "usageHint": "body",
                            }
                        },
                    },
                    _progress_image("img2", 14.7, "critical"),
                    {
                        "id": "val2",
                        "component": {
                            "Text": {
                                "text": {"literalString": "14.7% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row3",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl3", "img3", "val3"]},
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
                    _progress_image("img3", 14.1, "critical"),
                    {
                        "id": "val3",
                        "component": {
                            "Text": {
                                "text": {"literalString": "14.1% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button 1: flows FORWARD to PO Confirmed card
                    {
                        "id": "btn_reorder",
                        "component": {
                            "Button": {
                                "child": "btn_reorder_lbl",
                                "primary": True,
                                "action": {
                                    "name": "emergency_reorder",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Execute expedited purchase order for 18.8 kg of Barista Oat Milk at Downtown Flagship — PO confirmed"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_reorder_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Emergency Reorder: Oat Milk (6.2%)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    # Button 2: flows FORWARD to Consumption Analysis card
                    {
                        "id": "btn_analysis",
                        "component": {
                            "Button": {
                                "child": "btn_analysis_lbl",
                                "primary": False,
                                "action": {
                                    "name": "view_consumption",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": "Analyze consumption velocity and stockout timeline for Downtown Flagship Dark Roast beans"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_analysis_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "View Consumption Analysis"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ])


def build_po_confirmation_card(
    po_num: str = "PO-CYMBAL-8297",
    item: str = "Barista Edition Oat Milk",
    qty: str = "18.8 kg",
    cost: str = "$347.80",
    store: str = "Downtown Flagship",
    eta: str = "2 Hours (Expedited)",
    supplier: str = "Pacific Dairy Co.",
) -> list[dict[str, Any]]:
    """Build Expedited Purchase Order Confirmation Card (Card 2).

    Buttons flow FORWARD:
      - "Track Delivery" -> Delivery Tracking card (Card 5)
      - "Notify Store Manager" -> Notification Confirmed card (Card 4)
    """
    return normalize_a2ui_messages([
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
                                        "row_supplier",
                                        "row_eta",
                                        "divider2",
                                        "tracker_lbl",
                                        "tracker_val",
                                        "divider3",
                                        "btn_track",
                                        "btn_notify",
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
                                "text": {"literalString": f"{po_num} -- Expedited"},
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
                        "id": "row_supplier",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_supplier", "val_supplier"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_supplier",
                        "component": {
                            "Text": {"text": {"literalString": "Supplier:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_supplier",
                        "component": {
                            "Text": {"text": {"literalString": supplier}, "usageHint": "body"}
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
                        "id": "tracker_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Order Status:"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {
                        "id": "tracker_val",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[OK] Submitted  [OK] Approved  [ ] In Transit  [ ] Delivered"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider3", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button 1: flows FORWARD to Delivery Tracking card
                    {
                        "id": "btn_track",
                        "component": {
                            "Button": {
                                "child": "btn_track_lbl",
                                "primary": True,
                                "action": {
                                    "name": "track_delivery",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Track delivery status for {po_num} from Pacific Dairy Co. to {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_track_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Track Delivery"},
                                "usageHint": "body",
                            }
                        },
                    },
                    # Button 2: flows FORWARD to Notification Confirmed card
                    {
                        "id": "btn_notify",
                        "component": {
                            "Button": {
                                "child": "btn_notify_lbl",
                                "primary": False,
                                "action": {
                                    "name": "notify_manager",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Notify store manager that {po_num} has been placed and delivery is confirmed for {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_notify_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Notify Store Manager"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ])


def build_consumption_analysis_card(
    store: str = "Downtown Flagship",
    item: str = "Organic Dark Roast Beans",
    stock: str = "7.4 kg",
    rate: str = "1.2 kg/hr",
    hours: str = "6.2 Hours",
    reorder_qty: str = "40.0 kg",
) -> list[dict[str, Any]]:
    """Build Consumption Velocity & Stockout Analysis Card (Card 3).

    Buttons flow FORWARD:
      - "Execute Expedited PO" -> PO Confirmed card (Card 2)
    """
    return normalize_a2ui_messages([
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
                                        "rec_lbl",
                                        "rec_val",
                                        "divider3",
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
                                "text": {"literalString": f"{store} - {item}"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_stock",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_stock", "img_stock", "val_stock"]},
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
                    _progress_image("img_stock", 14.8, "critical"),
                    {
                        "id": "val_stock",
                        "component": {
                            "Text": {"text": {"literalString": stock}, "usageHint": "body"}
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
                                "text": {"literalString": f"{hours} -- CRITICAL"},
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
                        "id": "rec_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "AI Recommendation:"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {
                        "id": "rec_val",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Immediate reorder recommended -- projected stockout before peak hours (11am-2pm)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider3", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button: flows FORWARD to PO Confirmed card
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
                                                "literalString": f"Execute expedited PO for {reorder_qty} of {item} at {store} -- PO confirmed"
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
    ])


def build_notification_confirmed_card(
    store: str = "Downtown Flagship",
    manager: str = "Sarah Chen",
    po_num: str = "PO-CYMBAL-8297",
    items_flagged: str = "Barista Oat Milk (6.2%), Espresso Blend (14.7%)",
    eta: str = "2 hours",
) -> list[dict[str, Any]]:
    """Build Store Manager Notification Confirmed Card (Card 4 -- NEW).

    Shown after notify_store_manager tool is called.
    Buttons flow FORWARD:
      - "View Full Fleet Dashboard" -> Fleet Alert card (Card 1)
      - "Run Equipment Scan" -> Equipment Diagnostic card (Card 6)
    """
    return normalize_a2ui_messages([
        {"beginRendering": {"surfaceId": "notification_confirmed", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "notification_confirmed",
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
                                        "row_type",
                                        "row_items",
                                        "row_po",
                                        "row_eta",
                                        "divider2",
                                        "steps_lbl",
                                        "step1",
                                        "step2",
                                        "step3",
                                        "divider3",
                                        "btn_fleet",
                                        "btn_equipment",
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
                                "text": {"literalString": "Store Manager Notified"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {
                        "id": "sub",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"Alert sent to {manager} ({store} Manager)"},
                                "usageHint": "h4",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "row_type",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_type", "val_type"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_type",
                        "component": {
                            "Text": {"text": {"literalString": "Alert Type:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_type",
                        "component": {
                            "Text": {"text": {"literalString": "Critical Stockout Warning"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_items",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_items", "val_items"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_items",
                        "component": {
                            "Text": {"text": {"literalString": "Items Flagged:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_items",
                        "component": {
                            "Text": {"text": {"literalString": items_flagged}, "usageHint": "body"}
                        },
                    },
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
                            "Text": {"text": {"literalString": "PO Status:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_po",
                        "component": {
                            "Text": {"text": {"literalString": f"{po_num} dispatched"}, "usageHint": "body"}
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
                        "id": "steps_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Next Steps:"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {
                        "id": "step1",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[OK] Manager acknowledged via quick reply"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "step2",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[OK] Backup supplier (Oat Co.) contacted"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "step3",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[OK] Delivery tracking active"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider3", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button 1: back to Fleet Alert (Card 1)
                    {
                        "id": "btn_fleet",
                        "component": {
                            "Button": {
                                "child": "btn_fleet_lbl",
                                "primary": True,
                                "action": {
                                    "name": "view_fleet",
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
                        "id": "btn_fleet_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "View Full Fleet Dashboard"},
                                "usageHint": "body",
                            }
                        },
                    },
                    # Button 2: flows FORWARD to Equipment card
                    {
                        "id": "btn_equipment",
                        "component": {
                            "Button": {
                                "child": "btn_equipment_lbl",
                                "primary": False,
                                "action": {
                                    "name": "run_equipment_scan",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Detect equipment anomalies and run diagnostic scan at {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_equipment_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Run Equipment Scan"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ])


def build_delivery_tracking_card(
    po_num: str = "PO-CYMBAL-8297",
    store: str = "Downtown Flagship",
    carrier: str = "Pacific Express",
    driver: str = "Miguel R.",
    eta: str = "10:30 AM (15 min away)",
    item: str = "Barista Edition Oat Milk",
) -> list[dict[str, Any]]:
    """Build Delivery Tracking Card (Card 5 -- NEW).

    Shown when user clicks 'Track Delivery' on the PO Confirmation card.
    Buttons flow FORWARD:
      - "Notify Store Manager" -> Notification Confirmed card (Card 4)
      - "View Fleet Dashboard" -> Fleet Alert card (Card 1)
    """
    return normalize_a2ui_messages([
        {"beginRendering": {"surfaceId": "delivery_tracking", "root": "card"}},
        {
            "surfaceUpdate": {
                "surfaceId": "delivery_tracking",
                "components": [
                    {"id": "card", "component": {"Card": {"child": "col"}}},
                    {
                        "id": "col",
                        "component": {
                            "Column": {
                                "children": {
                                    "explicitList": [
                                        "title",
                                        "divider1",
                                        "tracker_lbl",
                                        "tracker_val",
                                        "divider2",
                                        "row_po",
                                        "row_item",
                                        "row_store",
                                        "row_carrier",
                                        "row_driver",
                                        "row_eta",
                                        "divider3",
                                        "btn_notify",
                                        "btn_fleet",
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
                                "text": {"literalString": "Delivery Tracking"},
                                "usageHint": "h2",
                            }
                        },
                    },
                    {"id": "divider1", "component": {"Divider": {"axis": "horizontal"}}},
                    {
                        "id": "tracker_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Order Progress:"},
                                "usageHint": "caption",
                            }
                        },
                    },
                    {
                        "id": "tracker_val",
                        "component": {
                            "Text": {
                                "text": {"literalString": "[OK] Submitted  [OK] Approved  [>>] In Transit  [ ] Delivered"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
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
                            "Text": {"text": {"literalString": "Item:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_item",
                        "component": {
                            "Text": {"text": {"literalString": item}, "usageHint": "body"}
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
                            "Text": {"text": {"literalString": "Destination:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_store",
                        "component": {
                            "Text": {"text": {"literalString": store}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_carrier",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_carrier", "val_carrier"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_carrier",
                        "component": {
                            "Text": {"text": {"literalString": "Carrier:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_carrier",
                        "component": {
                            "Text": {"text": {"literalString": carrier}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "row_driver",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_driver", "val_driver"]},
                                "distribution": "spaceBetween",
                            }
                        },
                    },
                    {
                        "id": "lbl_driver",
                        "component": {
                            "Text": {"text": {"literalString": "Driver:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_driver",
                        "component": {
                            "Text": {"text": {"literalString": driver}, "usageHint": "body"}
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
                            "Text": {"text": {"literalString": "ETA:"}, "usageHint": "body"}
                        },
                    },
                    {
                        "id": "val_eta",
                        "component": {
                            "Text": {"text": {"literalString": eta}, "usageHint": "body"}
                        },
                    },
                    {"id": "divider3", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button 1: flows FORWARD to Notification card
                    {
                        "id": "btn_notify",
                        "component": {
                            "Button": {
                                "child": "btn_notify_lbl",
                                "primary": True,
                                "action": {
                                    "name": "notify_manager",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Notify store manager that delivery for {po_num} is in transit and arriving at {store}"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_notify_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Notify Store Manager"},
                                "usageHint": "body",
                            }
                        },
                    },
                    # Button 2: back to Fleet Alert card
                    {
                        "id": "btn_fleet",
                        "component": {
                            "Button": {
                                "child": "btn_fleet_lbl",
                                "primary": False,
                                "action": {
                                    "name": "view_fleet",
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
                        "id": "btn_fleet_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "View Fleet Dashboard"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ])


def build_equipment_diagnostic_card(
    store: str = "SFO Terminal 2",
) -> list[dict[str, Any]]:
    """Build Equipment Diagnostic Card (Card 6).

    Buttons flow FORWARD:
      - "Schedule Maintenance" -> Notification Confirmed card (Card 4)
      - "Check Bean Inventory" -> Fleet Alert card (Card 1)
    """
    return normalize_a2ui_messages([
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
                                        "btn_maintenance",
                                        "btn_inventory",
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
                                "text": {"literalString": "42.5 degrees C -- Normal (< 65 degrees C)"},
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
                                "text": {"literalString": "3.8 degrees C -- Normal (2-5 degrees C)"},
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
                                "text": {"literalString": "9.2 Bar -- Optimal"},
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
                                "text": {"literalString": "0.02g -- Low (Normal)"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {"id": "divider2", "component": {"Divider": {"axis": "horizontal"}}},
                    # Button 1: flows to Notification Confirmed card
                    {
                        "id": "btn_maintenance",
                        "component": {
                            "Button": {
                                "child": "btn_maintenance_lbl",
                                "primary": True,
                                "action": {
                                    "name": "schedule_maintenance",
                                    "context": [
                                        {
                                            "key": "message",
                                            "value": {
                                                "literalString": f"Notify store manager to schedule preventive maintenance at {store} based on diagnostic results"
                                            },
                                        }
                                    ],
                                },
                            }
                        },
                    },
                    {
                        "id": "btn_maintenance_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": "Schedule Maintenance"},
                                "usageHint": "body",
                            }
                        },
                    },
                    # Button 2: back to Fleet Alert card
                    {
                        "id": "btn_inventory",
                        "component": {
                            "Button": {
                                "child": "btn_inventory_lbl",
                                "primary": False,
                                "action": {
                                    "name": "check_inventory",
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
                        "id": "btn_inventory_lbl",
                        "component": {
                            "Text": {
                                "text": {"literalString": f"Check {store} Bean Inventory"},
                                "usageHint": "body",
                            }
                        },
                    },
                ],
            }
        },
    ])


def build_visual_chart_card(
    store: str = "Downtown Flagship",
) -> list[dict[str, Any]]:
    """Build Visual Telemetry Bar Chart Card."""
    return normalize_a2ui_messages([
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
                                "children": {"explicitList": ["lbl_oat", "img_oat", "val_oat"]},
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
                    _progress_image("img_oat", 6.2, "critical"),
                    {
                        "id": "val_oat",
                        "component": {
                            "Text": {
                                "text": {"literalString": "6.2% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_esp",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_esp", "img_esp", "val_esp"]},
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
                    _progress_image("img_esp", 14.7, "critical"),
                    {
                        "id": "val_esp",
                        "component": {
                            "Text": {
                                "text": {"literalString": "14.7% CRITICAL"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_dark",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_dark", "img_dark", "val_dark"]},
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
                    _progress_image("img_dark", 23.0, "warning"),
                    {
                        "id": "val_dark",
                        "component": {
                            "Text": {
                                "text": {"literalString": "23.0% WARNING"},
                                "usageHint": "body",
                            }
                        },
                    },
                    {
                        "id": "row_milk",
                        "component": {
                            "Row": {
                                "children": {"explicitList": ["lbl_milk", "img_milk", "val_milk"]},
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
                    _progress_image("img_milk", 88.5, "healthy"),
                    {
                        "id": "val_milk",
                        "component": {
                            "Text": {
                                "text": {"literalString": "88.5% HEALTHY"},
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
                                                "literalString": "Execute expedited purchase order for Barista Oat Milk (6.2%) at Downtown Flagship -- PO confirmed"
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
    ])


def get_scenario_card(query: str, text: str = "") -> list[dict[str, Any]]:
    """Match query intent to demo scenario card.

    Demo flow:
      Fleet Alert (Card 1) -> PO Confirmed (Card 2) -> Delivery Tracking (Card 5)
                           -> Consumption (Card 3)   -> PO Confirmed (Card 2)
                                                              -> Manager Notified (Card 4)
      Equipment (Card 6)  -> Manager Notified (Card 4) -> Fleet Alert (Card 1)
    """
    q = (query + " " + text).lower()

    # Card 5: Delivery Tracking — match before PO confirmed to catch "track delivery"
    if any(k in q for k in ["track delivery", "tracking", "in transit", "driver", "carrier", "pacific express", "15 min away"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        po_match = re.search(r"PO-[A-Z0-9-]+", text)
        po_num = po_match.group(0) if po_match else "PO-CYMBAL-8297"
        item = "Organic Dark Roast Beans" if "dark roast" in q else "Barista Edition Oat Milk"
        return build_delivery_tracking_card(po_num=po_num, store=store, item=item)

    # Card 4: Notification Confirmed — match after delivery tracking
    if any(k in q for k in ["notify store manager", "manager notified", "alert sent", "notification confirmed", "sarah chen", "next steps"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        po_match = re.search(r"PO-[A-Z0-9-]+", text)
        po_num = po_match.group(0) if po_match else "PO-CYMBAL-8297"
        items = "Organic Dark Roast Beans (14.1%)" if "dark roast" in q or "sfo" in q else "Barista Oat Milk (6.2%), Espresso Blend (14.7%)"
        return build_notification_confirmed_card(store=store, po_num=po_num, items_flagged=items)

    # Card 2: PO Confirmed
    if any(k in q for k in ["purchase order", "po-", "po confirmed", "order confirmed", "order created", "submitted", "expedited po", "18.8 kg", "40.0 kg"]):
        po_match = re.search(r"PO-[A-Z0-9-]+", text)
        po_num = po_match.group(0) if po_match else "PO-CYMBAL-8297"
        is_dark_roast = "dark roast" in q or "40" in q
        item = "Organic Dark Roast Beans" if is_dark_roast else "Barista Edition Oat Milk"
        qty = "40.0 kg" if is_dark_roast else "18.8 kg"
        cost = "$740.00" if is_dark_roast else "$347.80"
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        supplier = "Pacific Coffee Distributors" if is_dark_roast else "Pacific Dairy Co."
        return build_po_confirmation_card(
            po_num=po_num, item=item, qty=qty, cost=cost, store=store, supplier=supplier
        )

    # Card 3: Consumption Analysis
    if any(k in q for k in ["consumption", "velocity", "stockout", "burn rate", "analyze"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        item = "Barista Edition Oat Milk" if "oat" in q else "Organic Dark Roast Beans"
        return build_consumption_analysis_card(store=store, item=item)

    # Card 6: Equipment Diagnostic
    if any(k in q for k in ["diagnostic", "anomaly", "anomalies", "temperature", "spike", "equipment", "health", "grinder", "chiller", "pump"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        return build_equipment_diagnostic_card(store=store)

    # Visual Chart (bonus card for chart/graph requests)
    if any(k in q for k in ["chart", "graph", "bar chart", "visual"]):
        store = "SFO Terminal 2" if "sfo" in q or "airport" in q else "Downtown Flagship"
        return build_visual_chart_card(store=store)

    # Card 1: Default — Fleet Inventory Telemetry
    return build_fleet_inventory_card()
