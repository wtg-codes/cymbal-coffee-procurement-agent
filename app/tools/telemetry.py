# Copyright 2026 Google LLC

import datetime
from typing import Any

STORE_TELEMETRY: dict[str, dict[str, Any]] = {
    "downtown-flagship": {
        "store_name": "Downtown Flagship (#101)",
        "city": "San Francisco, CA",
        "address": "100 Market St",
        "bins": {
            "dark-roast-beans": {
                "item_name": "Organic Dark Roast Beans",
                "bin_id": "BIN-SF101-01",
                "level_percent": 82.0,
                "current_weight_kg": 16.4,
                "max_capacity_kg": 20.0,
                "temp_celsius": 21.5,
                "pressure_bar": 1.02,
                "status": "OPTIMAL",
                "hourly_consumption_kg": 1.2,
            },
            "espresso-blend": {
                "item_name": "Signature Espresso Blend",
                "bin_id": "BIN-SF101-02",
                "level_percent": 65.0,
                "current_weight_kg": 13.0,
                "max_capacity_kg": 20.0,
                "temp_celsius": 22.0,
                "pressure_bar": 1.01,
                "status": "OPTIMAL",
                "hourly_consumption_kg": 1.8,
            },
            "oat-milk": {
                "item_name": "Barista Edition Oat Milk",
                "bin_id": "CONT-SF101-03",
                "level_percent": 45.0,
                "current_weight_kg": 9.0,
                "max_capacity_kg": 20.0,
                "temp_celsius": 3.8,
                "pressure_bar": 1.05,
                "status": "OPTIMAL",
                "hourly_consumption_kg": 2.1,
            },
        },
        "anomalies": [],
    },
    "airport-express": {
        "store_name": "SFO Terminal 2 (#102)",
        "city": "San Francisco, CA",
        "address": "SFO Airport Gate 54",
        "bins": {
            "dark-roast-beans": {
                "item_name": "Organic Dark Roast Beans",
                "bin_id": "BIN-SF102-01",
                "level_percent": 15.0,
                "current_weight_kg": 3.0,
                "max_capacity_kg": 20.0,
                "temp_celsius": 21.8,
                "pressure_bar": 0.98,
                "status": "WARNING",
                "hourly_consumption_kg": 2.5,
            },
            "espresso-blend": {
                "item_name": "Signature Espresso Blend",
                "bin_id": "BIN-SF102-02",
                "level_percent": 90.0,
                "current_weight_kg": 18.0,
                "max_capacity_kg": 20.0,
                "temp_celsius": 21.2,
                "pressure_bar": 1.03,
                "status": "OPTIMAL",
                "hourly_consumption_kg": 3.0,
            },
        },
        "anomalies": [],
    },
}


def get_bin_telemetry(store_id: str = "all") -> dict[str, Any]:
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if store_id.lower() in ("all", "all-stores"):
        return {
            "mode": "ALL_LOCATIONS",
            "timestamp": timestamp,
            "total_stores": len(STORE_TELEMETRY),
            "stores": STORE_TELEMETRY,
        }

    store = STORE_TELEMETRY.get(store_id)
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}

    return {
        "store_id": store_id,
        "store_name": store["store_name"],
        "timestamp": timestamp,
        "bins": store["bins"],
    }


def simulate_sensor_event(
    store_id: str = "downtown-flagship",
    item_key: str = "dark-roast-beans",
    new_level_percent: float = 12.0,
) -> dict[str, Any]:
    store = STORE_TELEMETRY.get(store_id)
    if not store or item_key not in store["bins"]:
        return {"error": f"Item '{item_key}' not found."}

    target = store["bins"][item_key]
    target["level_percent"] = new_level_percent
    target["current_weight_kg"] = round((new_level_percent / 100.0) * target["max_capacity_kg"], 1)
    target["status"] = "CRITICAL" if new_level_percent <= 15.0 else "OPTIMAL"

    return {
        "event": "IOT_SENSOR_TELEMETRY_UPDATED",
        "store_id": store_id,
        "item_name": target["item_name"],
        "new_level_percent": target["level_percent"],
        "status": target["status"],
    }


def detect_equipment_anomalies(store_id: str = "downtown-flagship") -> dict[str, Any]:
    store = STORE_TELEMETRY.get(store_id)
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}
    return {
        "store_id": store_id,
        "health_status": "ALL_SYSTEMS_HEALTHY",
        "detected_anomalies": [],
    }

