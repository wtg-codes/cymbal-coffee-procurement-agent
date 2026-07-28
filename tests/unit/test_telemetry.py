# Copyright 2026 Google LLC

import datetime

from app.tools.telemetry import (
    SIMULATION_STATE,
    check_backend_status,
    check_simulation_timeout,
    detect_equipment_anomalies,
    generate_telemetry_chart,
    get_bin_telemetry,
    get_simulation_status,
    resolve_store_id,
    simulate_sensor_event,
    start_simulation,
    stop_simulation,
    tick_simulation,
)


def test_simulation_lifecycle():
    """Test start, status, tick, and stop of simulation."""
    start_res = start_simulation(duration_minutes=30)
    assert start_res["status"] == "SIMULATION_STARTED"
    assert SIMULATION_STATE["is_active"] is True

    status_res = get_simulation_status()
    assert status_res["is_active"] is True
    assert status_res["remaining_seconds"] > 0

    tick_simulation()

    stop_res = stop_simulation()
    assert stop_res["status"] == "SIMULATION_STOPPED"
    assert SIMULATION_STATE["is_active"] is False

    status_stopped = get_simulation_status()
    assert status_stopped["is_active"] is False


def test_simulation_timeout():
    """Test simulation timeout expiration behavior."""
    start_simulation(duration_minutes=1)
    SIMULATION_STATE["expires_at"] = datetime.datetime.now(
        datetime.UTC
    ) - datetime.timedelta(seconds=10)
    expired = check_simulation_timeout()
    assert expired is True
    assert SIMULATION_STATE["is_active"] is False


def test_get_bin_telemetry_all_and_specific():
    """Test get_bin_telemetry for all stores, specific store, and invalid store."""
    all_res = get_bin_telemetry("all")
    assert all_res["mode"] == "ALL_LOCATIONS"
    assert "downtown-flagship" in all_res["stores"]

    specific_res = get_bin_telemetry("downtown-flagship")
    assert specific_res["store_id"] == "downtown-flagship"
    assert "bins" in specific_res

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


def test_check_backend_status():
    """Test check_backend_status and check_cloud_run_backend_health structure."""
    res = check_backend_status()
    assert "status" in res
    assert "dashboard_url" in res
    assert "health_endpoint" in res
    assert res["status"] in ("ONLINE", "OFFLINE")
