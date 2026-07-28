# Copyright 2026 Google LLC

import datetime
import os
import urllib.request
from typing import Any

CLOUD_RUN_DASHBOARD_URL = os.getenv(
    "CLOUD_RUN_DASHBOARD_URL",
    "https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app"
)

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


def check_cloud_run_backend_health(url: str = CLOUD_RUN_DASHBOARD_URL) -> dict[str, Any]:
    """Check if the Cloud Run synthetic telemetry & dashboard backend is online and responding."""
    base_url = url.rstrip("/")
    endpoints_to_check = [f"{base_url}/health", f"{base_url}/api/dashboard/data", f"{base_url}/"]
    dashboard_url = f"{base_url}/dashboard"

    last_error = None
    for endpoint in endpoints_to_check:
        try:
            req = urllib.request.Request(endpoint, headers={"User-Agent": "Cymbal-Procurement-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=3) as res:
                if res.status in (200, 301, 302, 307, 308):
                    return {
                        "is_online": True,
                        "status": "ONLINE",
                        "dashboard_url": dashboard_url,
                        "health_endpoint": endpoint,
                        "http_code": res.status,
                        "message": f"Cloud Run telemetry backend is ONLINE at {dashboard_url}"
                    }
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "is_online": False,
        "status": "OFFLINE",
        "dashboard_url": dashboard_url,
        "health_endpoint": f"{base_url}/health",
        "error": last_error,
        "user_action_required": f"⚠️ Cloud Run Synthetic Data Backend at {dashboard_url} is unreachable."
    }


def check_backend_status() -> dict[str, Any]:
    """Check the operational status of the Cloud Run synthetic data backend service."""
    return check_cloud_run_backend_health()


def resolve_store_id(store_id: str) -> str | None:
    """Fuzzy-resolve store_id or store name to internal store key."""
    if not store_id:
        return "downtown-flagship"
    s = store_id.lower().strip()
    if s in STORE_TELEMETRY:
        return s
    if "downtown" in s or "101" in s or "flagship" in s:
        return "downtown-flagship"
    if "airport" in s or "sfo" in s or "102" in s or "express" in s:
        return "airport-express"
    return None


def get_bin_telemetry(store_id: str = "all") -> dict[str, Any]:
    check_simulation_timeout()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    backend_health = check_cloud_run_backend_health()

    if store_id.lower() in ("all", "all-stores"):
        return {
            "mode": "ALL_LOCATIONS",
            "timestamp": timestamp,
            "total_stores": len(STORE_TELEMETRY),
            "stores": STORE_TELEMETRY,
            "simulation": get_simulation_status(),
            "cloud_run_backend": backend_health,
        }

    key = resolve_store_id(store_id)
    store = STORE_TELEMETRY.get(key) if key else None
    if not store:
        return {"error": f"Store ID '{store_id}' not found.", "cloud_run_backend": backend_health}

    return {
        "store_id": key,
        "store_name": store["store_name"],
        "timestamp": timestamp,
        "bins": store["bins"],
        "simulation": get_simulation_status(),
        "cloud_run_backend": backend_health,
    }


def simulate_sensor_event(
    store_id: str = "downtown-flagship",
    item_key: str = "dark-roast-beans",
    new_level_percent: float = 12.0,
) -> dict[str, Any]:
    key = resolve_store_id(store_id) or "downtown-flagship"
    store = STORE_TELEMETRY.get(key)
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
        "store_id": key,
        "item_name": target["item_name"],
        "new_level_percent": target["level_percent"],
        "status": target["status"],
    }


def detect_equipment_anomalies(store_id: str = "downtown-flagship") -> dict[str, Any]:
    key = resolve_store_id(store_id)
    if not key:
        return {"error": f"Store ID '{store_id}' not found."}
    store = STORE_TELEMETRY.get(key)
    if not store:
        return {"error": f"Store ID '{store_id}' not found."}
    return {
        "store_id": key,
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

