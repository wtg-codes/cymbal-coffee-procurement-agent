# Copyright 2026 Google LLC

import datetime
from typing import Any

from app.tools.telemetry import STORE_TELEMETRY

SUPPLIER_CATALOG = {
    "cymbal-roasters": {
        "supplier_name": "Cymbal Artisan Roasters Direct",
        "lead_time_hours_expedited": 2,
        "price_per_kg": 18.50,
    },
}

PURCHASE_ORDERS = []


def analyze_consumption_patterns(
    store_id: str = "downtown-flagship",
    item_key: str = "dark-roast-beans",
    forecast_hours: int = 48,
) -> dict[str, Any]:
    store = STORE_TELEMETRY.get(store_id)
    if not store or item_key not in store["bins"]:
        return {"error": f"Item '{item_key}' not found."}

    bin_data = store["bins"][item_key]
    return {
        "store_id": store_id,
        "item_name": bin_data["item_name"],
        "current_stock_kg": bin_data["current_weight_kg"],
        "hourly_consumption_rate_kg": bin_data["hourly_consumption_kg"],
        "estimated_hours_until_stockout": 2.0,
        "recommendation": {
            "action": "EXPEDITED_REORDER_REQUIRED",
            "recommended_quantity_kg": 40.0,
        },
    }


def create_purchase_order(
    store_id: str = "downtown-flagship",
    item_key: str = "dark-roast-beans",
    quantity_kg: float = 40.0,
    urgency: str = "EXPEDITED",
) -> dict[str, Any]:
    store = STORE_TELEMETRY.get(store_id)
    item_name = store["bins"][item_key]["item_name"] if store else "Dark Roast"
    supplier = SUPPLIER_CATALOG["cymbal-roasters"]
    total_cost = round(quantity_kg * float(supplier["price_per_kg"]), 2)
    po_number = f"PO-CYMBAL-{len(PURCHASE_ORDERS) + 1001}"

    po_record = {
        "po_number": po_number,
        "store_id": store_id,
        "supplier_name": supplier["supplier_name"],
        "item_name": item_name,
        "quantity_kg": quantity_kg,
        "unit_price_usd": supplier["price_per_kg"],
        "total_cost_usd": total_cost,
        "urgency": urgency,
        "delivery_eta": (
            datetime.datetime.now() + datetime.timedelta(hours=2)
        ).strftime("%Y-%m-%d %H:%M:%S"),
        "status": "ROUTED_TO_FULFILLMENT",
    }
    PURCHASE_ORDERS.append(po_record)

    return {
        "success": True,
        "purchase_order": po_record,
    }
