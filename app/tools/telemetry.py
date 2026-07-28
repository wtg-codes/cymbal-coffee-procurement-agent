# Copyright 2026 Google LLC

import datetime
from typing import Any

from app.database import get_all_stores_telemetry, update_sensor_level

STORE_TELEMETRY = get_all_stores_telemetry()

# ---------------------------------------------------------------------------
# Always-on simulation engine
# The simulation starts the moment this module is imported. There is no on/off
# switch — stores always have a background trickle of orders consuming stock.
# Event modes (rush, catering, lull) temporarily change the consumption rate.
# ---------------------------------------------------------------------------

_EVENT_MODES = {
    "normal": {"label": "Normal Operations", "multiplier": 1.0},
    "morning_rush": {"label": "☕ Morning Rush", "multiplier": 4.5},
    "afternoon_lull": {"label": "😴 Afternoon Lull", "multiplier": 0.25},
    "catering_event": {"label": "🎉 Catering Event", "multiplier": 8.0},
    "weekend_surge": {"label": "📈 Weekend Surge", "multiplier": 3.0},
}

SIMULATION_STATE: dict[str, Any] = {
    "started_at": datetime.datetime.now(datetime.UTC),
    "last_tick_at": None,
    "event_mode": "normal",
    "event_started_at": None,
    "event_duration_seconds": 0,
    "simulated_orders": [],
    "total_orders_processed": 0,
}

# Base hourly consumption rates (kg) per store per bin at normal trickle
_BASE_RATES: dict[str, dict[str, float]] = {
    "downtown-flagship":  {"dark-roast-beans": 0.15, "espresso-blend": 0.12, "oat-milk": 0.18},
    "airport-express":    {"dark-roast-beans": 0.10, "espresso-blend": 0.08, "oat-milk": 0.09},
    "financial-district": {"dark-roast-beans": 0.08, "espresso-blend": 0.10, "oat-milk": 0.07},
    "mission-roastery":   {"dark-roast-beans": 0.12, "espresso-blend": 0.09, "oat-milk": 0.06},
    "union-square":       {"dark-roast-beans": 0.09, "espresso-blend": 0.07, "oat-milk": 0.11},
}

_ORDER_TEMPLATES = [
    ("Oat Milk Lattes",         "downtown-flagship",  "oat-milk"),
    ("Double Espresso Shots",   "downtown-flagship",  "espresso-blend"),
    ("Cold Brew Bottled",       "airport-express",    "dark-roast-beans"),
    ("Cappuccinos",             "downtown-flagship",  "oat-milk"),
    ("Drip Dark Roast",         "downtown-flagship",  "dark-roast-beans"),
    ("Flat Whites",             "financial-district", "espresso-blend"),
    ("Pour-Overs",              "mission-roastery",   "dark-roast-beans"),
    ("Iced Lattes",             "union-square",       "oat-milk"),
    ("Cortados",                "airport-express",    "espresso-blend"),
    ("Batch Brew (Catering)",   "downtown-flagship",  "dark-roast-beans"),
]


def _active_multiplier() -> float:
    """Return the current consumption multiplier, reverting expired events to normal."""
    mode = SIMULATION_STATE["event_mode"]
    if mode == "normal":
        return 1.0
    started = SIMULATION_STATE.get("event_started_at")
    duration = SIMULATION_STATE.get("event_duration_seconds", 0)
    if started and duration:
        elapsed = (datetime.datetime.now(datetime.UTC) - started).total_seconds()
        if elapsed >= duration:
            SIMULATION_STATE["event_mode"] = "normal"
            SIMULATION_STATE["event_started_at"] = None
            SIMULATION_STATE["event_duration_seconds"] = 0
            return 1.0
    return _EVENT_MODES.get(mode, {}).get("multiplier", 1.0)


def tick_simulation() -> None:
    """Consume stock based on real elapsed time and current event mode."""
    now = datetime.datetime.now(datetime.UTC)
    last = SIMULATION_STATE["last_tick_at"]
    if last is None:
        SIMULATION_STATE["last_tick_at"] = now
        return

    elapsed_hours = (now - last).total_seconds() / 3600.0
    if elapsed_hours < 0.00027:  # Less than ~1 second — skip
        return

    SIMULATION_STATE["last_tick_at"] = now
    multiplier = _active_multiplier()
    all_stores = get_all_stores_telemetry()

    for store_key, rates in _BASE_RATES.items():
        store = all_stores.get(store_key)
        if not store:
            continue
        for bin_key, base_kg_per_hour in rates.items():
            bin_data = store["bins"].get(bin_key)
            if not bin_data:
                continue
            consumed = base_kg_per_hour * elapsed_hours * multiplier
            current = bin_data["current_weight_kg"]
            max_cap = bin_data["max_capacity_kg"]
            new_weight = max(0.5, round(current - consumed, 2))
            update_sensor_level(store_key, bin_key, round((new_weight / max_cap) * 100, 1))

    # Append a synthetic order entry
    orders = SIMULATION_STATE.get("simulated_orders", [])
    template = _ORDER_TEMPLATES[len(orders) % len(_ORDER_TEMPLATES)]
    qty = int(8 + multiplier * 4)
    orders.insert(0, {
        "id": f"ORD-{1000 + SIMULATION_STATE['total_orders_processed']}",
        "time": now.strftime("%I:%M %p"),
        "description": f"{qty}x {template[0]}",
        "store_id": template[1],
        "bin": template[2],
        "mode": SIMULATION_STATE["event_mode"],
    })
    SIMULATION_STATE["simulated_orders"] = orders[:30]
    SIMULATION_STATE["total_orders_processed"] += qty


# Auto-start trickle when module loads
SIMULATION_STATE["last_tick_at"] = datetime.datetime.now(datetime.UTC)


def get_simulation_status() -> dict[str, Any]:
    """Return current simulation state."""
    tick_simulation()
    mode = SIMULATION_STATE["event_mode"]
    info = _EVENT_MODES.get(mode, _EVENT_MODES["normal"])
    remaining = 0
    started = SIMULATION_STATE.get("event_started_at")
    duration = SIMULATION_STATE.get("event_duration_seconds", 0)
    if started and duration:
        elapsed = (datetime.datetime.now(datetime.UTC) - started).total_seconds()
        remaining = max(0, int(duration - elapsed))
    return {
        "always_on": True,
        "event_mode": mode,
        "event_label": info["label"],
        "multiplier": info["multiplier"],
        "event_remaining_seconds": remaining,
        "total_orders_processed": SIMULATION_STATE["total_orders_processed"],
        "recent_orders": SIMULATION_STATE["simulated_orders"][:5],
        "uptime_seconds": int(
            (datetime.datetime.now(datetime.UTC) - SIMULATION_STATE["started_at"]).total_seconds()
        ),
    }


def trigger_event(
    event_mode: str = "morning_rush",
    duration_minutes: int = 15,
) -> dict[str, Any]:
    """Trigger a consumption event (morning_rush, catering_event, afternoon_lull,
    weekend_surge) for a limited duration. The simulation always runs — this just
    changes the rate temporarily.

    Args:
        event_mode: One of 'morning_rush', 'catering_event', 'afternoon_lull',
            'weekend_surge'. Use 'normal' to reset to baseline.
        duration_minutes: How long the event lasts (1-120 minutes).
    """
    duration_minutes = min(max(1, duration_minutes), 120)
    if event_mode not in _EVENT_MODES:
        return {"error": f"Unknown event mode '{event_mode}'. Valid: {list(_EVENT_MODES.keys())}"}

    SIMULATION_STATE["event_mode"] = event_mode
    SIMULATION_STATE["event_started_at"] = datetime.datetime.now(datetime.UTC)
    SIMULATION_STATE["event_duration_seconds"] = duration_minutes * 60
    tick_simulation()

    info = _EVENT_MODES[event_mode]
    return {
        "status": "EVENT_TRIGGERED",
        "event_mode": event_mode,
        "event_label": info["label"],
        "multiplier": info["multiplier"],
        "duration_minutes": duration_minutes,
        "description": f"Consumption rate is now {info['multiplier']}x normal for {duration_minutes} minutes.",
    }


# Keep start_simulation / stop_simulation as thin shims so existing tests don't break
def start_simulation(duration_minutes: int = 120) -> dict[str, Any]:
    """Alias for trigger_event('morning_rush'). Simulation is always-on."""
    return trigger_event("morning_rush", min(duration_minutes, 120))


def stop_simulation() -> dict[str, Any]:
    """Reset event mode to normal trickle. Simulation stays always-on."""
    return trigger_event("normal", 120)



def resolve_store_id(store_id: str) -> str | None:
    """Fuzzy-resolve store_id or store name to internal store key."""
    if not store_id:
        return "downtown-flagship"
    s = store_id.lower().strip()
    all_stores = get_all_stores_telemetry()
    if s in all_stores:
        return s
    if "downtown" in s or "101" in s or "flagship" in s:
        return "downtown-flagship"
    if "airport" in s or "sfo" in s or "102" in s or "express" in s:
        return "airport-express"
    if "financial" in s or "california" in s or "103" in s:
        return "financial-district"
    if "mission" in s or "roastery" in s or "104" in s:
        return "mission-roastery"
    if "union" in s or "powell" in s or "105" in s:
        return "union-square"
    return None


def get_bin_telemetry(store_id: str = "all") -> dict[str, Any]:
    """Get real-time IoT bin telemetry from all 5 store locations."""
    tick_simulation()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_stores = get_all_stores_telemetry()

    if not store_id or store_id.lower() in ("all", "all-stores", "across all stores"):
        return {
            "mode": "ALL_LOCATIONS",
            "timestamp": timestamp,
            "total_stores": len(all_stores),
            "stores": all_stores,
            "simulation": get_simulation_status(),
        }

    key = resolve_store_id(store_id)
    store = all_stores.get(key) if key else None
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}

    return {
        "store_id": key,
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
    """Simulate an IoT sensor level change and persist in SQLite database."""
    key = resolve_store_id(store_id) or "downtown-flagship"
    result = update_sensor_level(key, item_key, new_level_percent)
    return result


def detect_equipment_anomalies(store_id: str = "all") -> dict[str, Any]:
    """Scan equipment health and detect anomalies for a specific store or all 5 stores."""
    all_stores = get_all_stores_telemetry()
    if not store_id or store_id.lower() in ("all", "all-stores", "across all stores"):
        results = {}
        for s_key, s_data in all_stores.items():
            results[s_key] = {
                "store_name": s_data["store_name"],
                "health_status": "ALL_SYSTEMS_HEALTHY",
                "detected_anomalies": [],
            }
        return {
            "mode": "ALL_LOCATIONS",
            "total_stores_scanned": len(results),
            "stores": results,
        }

    key = resolve_store_id(store_id)
    if not key:
        return {"error": f"Store ID '{store_id}' not found."}
    store = all_stores.get(key)
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}
    return {
        "store_id": key,
        "store_name": store["store_name"],
        "health_status": "ALL_SYSTEMS_HEALTHY",
        "detected_anomalies": [],
    }


def _build_svg_bar_chart(items: list[dict[str, Any]]) -> str:
    svg_height = 140
    svg_width = 340
    bar_height = 22
    gap = 12
    start_y = 10

    bars_xml = []
    y = start_y
    for item in items:
        percent = item["percent"]
        bar_w = int((percent / 100.0) * 190)
        color = item["color"]
        name = item["name"]
        if len(name) > 18:
            name = name[:16] + ".."

        bars_xml.append(
            f'<text x="5" y="{y + 15}" fill="#cbd5e1" font-size="11" font-weight="500">{name}</text>'
            f'<rect x="110" y="{y}" width="190" height="{bar_height}" rx="4" fill="#1e293b"/>'
            f'<rect x="110" y="{y}" width="{bar_w}" height="{bar_height}" rx="4" fill="{color}"/>'
            f'<text x="{115 + bar_w}" y="{y + 15}" fill="#f8fafc" font-size="11" font-weight="700">{percent}%</text>'
        )
        y += bar_height + gap

    return f'<svg width="100%" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}" xmlns="http://www.w3.org/2000/svg">{"".join(bars_xml)}</svg>'


def _build_svg_pie_chart(items: list[dict[str, Any]], is_donut: bool = False) -> str:
    import math

    r = 45
    circumference = 2 * math.pi * r  # ~282.74
    total_val = sum(i["percent"] for i in items) or 1.0

    stroke_w = 26 if is_donut else 46
    current_offset = 0.0
    circles = []
    legend_items = []

    for item in items:
        percent = item["percent"]
        fraction = percent / total_val
        dash_len = fraction * circumference
        gap_len = circumference - dash_len
        color = item["color"]

        circles.append(
            f'<circle cx="75" cy="75" r="{r}" fill="transparent" stroke="{color}" '
            f'stroke-width="{stroke_w}" stroke-dasharray="{dash_len:.2f} {gap_len:.2f}" '
            f'stroke-dashoffset="{-current_offset:.2f}"/>'
        )

        legend_items.append(
            f'<div class="legend-item"><div class="color-box" style="background:{color};"></div>'
            f'<span>{item["name"]}: {percent}%</span></div>'
        )

        current_offset += dash_len

    return f'''<div style="display:flex; align-items:center; gap:20px;">
      <svg width="150" height="150" viewBox="0 0 150 150" style="transform: rotate(-90deg);" xmlns="http://www.w3.org/2000/svg">
        {"".join(circles)}
      </svg>
      <div style="display:flex; flex-direction:column; gap:8px;">
        {"".join(legend_items)}
      </div>
    </div>'''


def _build_svg_line_chart(items: list[dict[str, Any]]) -> str:
    svg_w, svg_h = 320, 120
    points = [(20, 85), (70, 70), (120, 35), (170, 55), (220, 20), (270, 10)]
    pts_str = " ".join(f"{x},{y}" for x, y in points)

    circles = "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="#f59e0b"/>' for x, y in points)

    return f'''<svg width="100%" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">
      <line x1="20" y1="100" x2="300" y2="100" stroke="#334155" stroke-width="1"/>
      <line x1="20" y1="10" x2="20" y2="100" stroke="#334155" stroke-width="1"/>
      <polyline points="{pts_str}" fill="none" stroke="#38bdf8" stroke-width="3"/>
      {circles}
      <text x="20" y="115" fill="#94a3b8" font-size="10">06:00</text>
      <text x="120" y="115" fill="#94a3b8" font-size="10">12:00</text>
      <text x="220" y="115" fill="#94a3b8" font-size="10">18:00</text>
    </svg>'''


def generate_telemetry_chart(
    store_id: str = "downtown-flagship",
    chart_type: str = "bar",
) -> dict[str, Any]:
    """Generate dynamic SVG chart markup (bar, pie, donut, line) for A2UI WebFrameSrcdoc rendering.

    Args:
        store_id: Target store identifier (e.g., 'downtown-flagship', 'airport-express').
        chart_type: Type of chart requested ('bar', 'pie', 'donut', 'line').
    """
    key = resolve_store_id(store_id) or "downtown-flagship"
    store = STORE_TELEMETRY.get(key, STORE_TELEMETRY["downtown-flagship"])
    store_name = store["store_name"]
    bins = store["bins"]

    chart_type_clean = chart_type.lower().strip()

    items = []
    colors = ["#38bdf8", "#f59e0b", "#10b981", "#a855f7", "#ec4899"]
    idx = 0
    for _item_key, b in bins.items():
        items.append({
            "name": b["item_name"],
            "percent": b["level_percent"],
            "weight": b["current_weight_kg"],
            "max": b["max_capacity_kg"],
            "rate": b.get("hourly_consumption_kg", 1.0),
            "color": colors[idx % len(colors)],
        })
        idx += 1

    if "pie" in chart_type_clean or "donut" in chart_type_clean:
        is_donut = "donut" in chart_type_clean
        svg_content = _build_svg_pie_chart(items, is_donut=is_donut)
    elif "line" in chart_type_clean:
        svg_content = _build_svg_line_chart(items)
    else:
        svg_content = _build_svg_bar_chart(items)

    html_srcdoc = f"""<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Security-Policy" content="connect-src 'none'">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #f8fafc; padding: 12px; font-size: 13px; }}
  .chart-container {{ width: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
  .chart-title {{ font-size: 13px; font-weight: 600; color: #94a3b8; margin-bottom: 10px; text-align: center; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: #cbd5e1; }}
  .color-box {{ width: 10px; height: 10px; border-radius: 2px; }}
</style>
</head>
<body>
  <div class="chart-container">
    <div class="chart-title">{store_name} - Telemetry ({chart_type.upper()})</div>
    {svg_content}
  </div>
</body>
</html>"""

    return {
        "store_id": key,
        "store_name": store_name,
        "chart_type": chart_type,
        "html_srcdoc": html_srcdoc,
        "a2ui_webframe_component": {
            "id": "telemetry_chart_iframe",
            "component": "WebFrameSrcdoc",
            "props": {
                "view_type": "AnalyticsChart",
                "height": 220,
                "srcdoc": {"literalString": html_srcdoc},
            },
        },
    }

