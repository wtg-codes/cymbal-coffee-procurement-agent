# Copyright 2026 Google LLC

from app.tools.telemetry import (
    SIMULATION_STATE,
    detect_equipment_anomalies,
    generate_telemetry_chart,
    get_bin_telemetry,
    get_simulation_status,
    resolve_store_id,
    simulate_sensor_event,
    start_simulation,
    stop_simulation,
    tick_simulation,
    trigger_event,
)


def test_simulation_always_on():
    """Simulation is always-on. Status always returns always_on=True."""
    status = get_simulation_status()
    assert status["always_on"] is True
    assert "event_mode" in status
    assert "multiplier" in status
    assert "total_orders_processed" in status


def test_trigger_event_modes():
    """Test all valid event modes via trigger_event."""
    for mode in ("morning_rush", "catering_event", "afternoon_lull", "weekend_surge", "normal"):
        res = trigger_event(event_mode=mode, duration_minutes=5)
        assert res["status"] == "EVENT_TRIGGERED"
        assert res["event_mode"] == mode
        assert res["multiplier"] > 0


def test_trigger_event_invalid():
    """Invalid event mode returns error."""
    res = trigger_event(event_mode="nonexistent_mode")
    assert "error" in res


def test_start_stop_shims():
    """start_simulation / stop_simulation are shims that still work."""
    start_res = start_simulation(duration_minutes=30)
    assert start_res["status"] == "EVENT_TRIGGERED"
    assert start_res["event_mode"] == "morning_rush"

    stop_res = stop_simulation()
    assert stop_res["status"] == "EVENT_TRIGGERED"
    assert stop_res["event_mode"] == "normal"


def test_tick_simulation():
    """Tick depletes stock over time."""
    import datetime

    SIMULATION_STATE["last_tick_at"] = (
        datetime.datetime.now(datetime.UTC) - datetime.timedelta(minutes=30)
    )
    tick_simulation()
    # After a 30-min tick, orders should have been appended
    assert SIMULATION_STATE["total_orders_processed"] > 0


def test_get_bin_telemetry_all_and_specific():
    """Test get_bin_telemetry for all stores, specific store, and invalid store."""
    all_res = get_bin_telemetry("all")
    assert all_res["mode"] == "ALL_LOCATIONS"
    assert "downtown-flagship" in all_res["stores"]
    # No cloud_run_backend key — backend is always-on, no health check
    assert "cloud_run_backend" not in all_res

    specific_res = get_bin_telemetry("downtown-flagship")
    assert specific_res["store_id"] == "downtown-flagship"
    assert "bins" in specific_res
    assert "cloud_run_backend" not in specific_res

    airport_res = get_bin_telemetry("airport-express")
    assert airport_res["store_id"] == "airport-express"

    invalid_res = get_bin_telemetry("non-existent-store")
    assert "error" in invalid_res


def test_resolve_store_id():
    """Test store ID fuzzy matching."""
    assert resolve_store_id("") == "downtown-flagship"
    assert resolve_store_id("downtown") == "downtown-flagship"
    assert resolve_store_id("sfo") == "airport-express"
    assert resolve_store_id("unknown_store") is None


def test_simulate_sensor_event():
    """Test simulate_sensor_event valid and invalid."""
    res_valid = simulate_sensor_event(
        store_id="downtown-flagship", item_key="dark-roast-beans", new_level_percent=12.0
    )
    assert res_valid["status"] == "CRITICAL"
    assert res_valid["new_level_percent"] == 12.0

    res_invalid = simulate_sensor_event(
        store_id="invalid-store", item_key="invalid-item", new_level_percent=5.0
    )
    assert "error" in res_invalid


def test_detect_equipment_anomalies():
    """Test detect_equipment_anomalies with valid and non-existent store."""
    res_valid = detect_equipment_anomalies("downtown-flagship")
    assert res_valid["store_id"] == "downtown-flagship"
    assert "detected_anomalies" in res_valid or "anomalies" in res_valid

    res_invalid = detect_equipment_anomalies("non-existent-store")
    assert "error" in res_invalid


def test_generate_telemetry_chart_types():
    """Test generate_telemetry_chart for bar, pie, donut, and line charts."""
    bar_res = generate_telemetry_chart(store_id="downtown-flagship", chart_type="bar")
    assert bar_res["chart_type"] == "bar"
    assert "<svg" in bar_res["html_srcdoc"]

    pie_res = generate_telemetry_chart(store_id="downtown-flagship", chart_type="pie")
    assert pie_res["chart_type"] == "pie"
    assert "<circle" in pie_res["html_srcdoc"]

    donut_res = generate_telemetry_chart(store_id="downtown-flagship", chart_type="donut")
    assert donut_res["chart_type"] == "donut"

    line_res = generate_telemetry_chart(store_id="downtown-flagship", chart_type="line")
    assert line_res["chart_type"] == "line"

    invalid_store = generate_telemetry_chart(store_id="unknown_store")
    assert invalid_store["store_id"] == "downtown-flagship"
