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


SIMULATION_STATE: dict[str, Any] = {
    "is_active": False,
    "started_at": None,
    "expires_at": None,
    "max_duration_seconds": 7200,  # 2 hours max
    "simulated_start_time": "06:30:00",
    "simulated_orders": [],
    "total_orders_processed": 0,
}


def check_simulation_timeout() -> bool:
    """Check if the simulation session has exceeded its 2-hour timeout and tick dynamic state."""
    if not SIMULATION_STATE["is_active"]:
        return False

    now = datetime.datetime.now(datetime.UTC)
    expires_at = SIMULATION_STATE.get("expires_at")

    if expires_at and now > expires_at:
        SIMULATION_STATE["is_active"] = False
        SIMULATION_STATE["started_at"] = None
        SIMULATION_STATE["expires_at"] = None
        return True

    # Tick dynamic order simulation if active
    tick_simulation()
    return SIMULATION_STATE["is_active"]


def tick_simulation() -> None:
    """Simulate continuous morning coffee orders depleting stock over time."""
    if not SIMULATION_STATE["is_active"] or not SIMULATION_STATE.get("started_at"):
        return

    now = datetime.datetime.now(datetime.UTC)
    elapsed_seconds = (now - SIMULATION_STATE["started_at"]).total_seconds()

    # Map 1 real second -> 1.5 simulated minutes of morning rush
    simulated_minutes = int(elapsed_seconds * 1.5)
    base_time = datetime.datetime.combine(datetime.date.today(), datetime.time(6, 30))
    sim_time = (base_time + datetime.timedelta(minutes=simulated_minutes)).strftime(
        "%I:%M %p"
    )

    # Gradual morning consumption curve per store
    # Downtown Flagship (#101) - Heavy morning rush
    df_beans = STORE_TELEMETRY["downtown-flagship"]["bins"]["dark-roast-beans"]
    df_espresso = STORE_TELEMETRY["downtown-flagship"]["bins"]["espresso-blend"]
    df_milk = STORE_TELEMETRY["downtown-flagship"]["bins"]["oat-milk"]

    # Calculate dynamic levels based on simulated minutes (starting from initial values)
    # Peak rush depletion: ~0.35% per simulated minute
    depletion_amount = min(75.0, round(simulated_minutes * 0.35, 1))

    new_df_beans = max(8.0, round(82.0 - depletion_amount, 1))
    new_df_espresso = max(15.0, round(65.0 - (depletion_amount * 0.8), 1))
    new_df_milk = max(6.0, round(45.0 - (depletion_amount * 0.9), 1))

    df_beans["level_percent"] = new_df_beans
    df_beans["current_weight_kg"] = round(
        (new_df_beans / 100.0) * df_beans["max_capacity_kg"], 1
    )
    df_beans["status"] = (
        "CRITICAL"
        if new_df_beans <= 15.0
        else ("WARNING" if new_df_beans <= 25.0 else "OPTIMAL")
    )

    df_espresso["level_percent"] = new_df_espresso
    df_espresso["current_weight_kg"] = round(
        (new_df_espresso / 100.0) * df_espresso["max_capacity_kg"], 1
    )
    df_espresso["status"] = (
        "CRITICAL"
        if new_df_espresso <= 15.0
        else ("WARNING" if new_df_espresso <= 25.0 else "OPTIMAL")
    )

    df_milk["level_percent"] = new_df_milk
    df_milk["current_weight_kg"] = round(
        (new_df_milk / 100.0) * df_milk["max_capacity_kg"], 1
    )
    df_milk["status"] = (
        "CRITICAL"
        if new_df_milk <= 15.0
        else ("WARNING" if new_df_milk <= 25.0 else "OPTIMAL")
    )

    # Generate synthetic order event log items
    orders = SIMULATION_STATE.get("simulated_orders", [])
    if len(orders) < min(50, simulated_minutes // 2 + 1):
        order_types = [
            ("16x Oat Milk Lattes", "downtown-flagship", -0.64, "oat-milk"),
            ("12x Double Espresso Shots", "downtown-flagship", -0.36, "espresso-blend"),
            ("8x Cold Brew Bottled", "airport-express", -0.40, "dark-roast-beans"),
            ("20x Cappuccinos", "downtown-flagship", -0.80, "oat-milk"),
            ("15x Drip Dark Roast", "downtown-flagship", -0.45, "dark-roast-beans"),
        ]
        item = order_types[len(orders) % len(order_types)]
        orders.insert(
            0,
            {
                "id": f"ORD-SF-{1000 + len(orders)}",
                "time": sim_time,
                "description": item[0],
                "store_id": item[1],
                "impact": f"{item[2]} kg",
                "status": "PROCESSING",
            },
        )
        SIMULATION_STATE["simulated_orders"] = orders[:20]  # Keep latest 20
        SIMULATION_STATE["total_orders_processed"] = len(orders) * 18


def start_simulation(duration_minutes: int = 120) -> dict[str, Any]:
    """Start synthetic demo simulation mode with a max 2-hour auto-timeout."""
    duration_minutes = min(max(1, duration_minutes), 120)  # Cap at 120 mins (2h max)
    now = datetime.datetime.now(datetime.UTC)
    expires_at = now + datetime.timedelta(minutes=duration_minutes)

    SIMULATION_STATE["is_active"] = True
    SIMULATION_STATE["started_at"] = now
    SIMULATION_STATE["expires_at"] = expires_at
    SIMULATION_STATE["simulated_orders"] = []
    SIMULATION_STATE["total_orders_processed"] = 0

    tick_simulation()

    return {
        "status": "SIMULATION_STARTED",
        "duration_minutes": duration_minutes,
        "expires_at": expires_at.isoformat(),
        "max_timeout": "2 hours max",
    }


def stop_simulation() -> dict[str, Any]:
    """Stop synthetic demo simulation mode."""
    SIMULATION_STATE["is_active"] = False
    SIMULATION_STATE["started_at"] = None
    SIMULATION_STATE["expires_at"] = None
    return {"status": "SIMULATION_STOPPED"}


def get_simulation_status() -> dict[str, Any]:
    """Get current simulation status and remaining time."""
    is_active = check_simulation_timeout()
    remaining_seconds = 0

    if is_active and SIMULATION_STATE.get("expires_at"):
        now = datetime.datetime.now(datetime.UTC)
        diff = (SIMULATION_STATE["expires_at"] - now).total_seconds()
        remaining_seconds = max(0, int(diff))

    return {
        "is_active": is_active,
        "remaining_seconds": remaining_seconds,
        "expires_at": SIMULATION_STATE["expires_at"].isoformat()
        if is_active and SIMULATION_STATE.get("expires_at")
        else None,
        "simulated_orders": SIMULATION_STATE.get("simulated_orders", []),
        "total_orders_processed": SIMULATION_STATE.get("total_orders_processed", 0),
    }


def get_bin_telemetry(store_id: str = "all") -> dict[str, Any]:
    check_simulation_timeout()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if store_id.lower() in ("all", "all-stores"):
        return {
            "mode": "ALL_LOCATIONS",
            "timestamp": timestamp,
            "total_stores": len(STORE_TELEMETRY),
            "stores": STORE_TELEMETRY,
            "simulation": get_simulation_status(),
        }

    store = STORE_TELEMETRY.get(store_id)
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}

    return {
        "store_id": store_id,
        "store_name": store["store_name"],
        "timestamp": timestamp,
        "bins": store["bins"],
        "simulation": get_simulation_status(),
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
    target["current_weight_kg"] = round(
        (new_level_percent / 100.0) * target["max_capacity_kg"], 1
    )
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
