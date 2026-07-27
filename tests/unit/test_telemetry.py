# Copyright 2026 Google LLC

import datetime

from app.tools.telemetry import (
    SIMULATION_STATE,
    check_simulation_timeout,
    detect_equipment_anomalies,
    get_bin_telemetry,
    get_simulation_status,
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


def test_get_bin_telemetry_all_and_invalid():
    """Test get_bin_telemetry for all stores and invalid store."""
    all_res = get_bin_telemetry("all")
    assert all_res["mode"] == "ALL_LOCATIONS"
    assert "downtown-flagship" in all_res["stores"]

    all_stores_res = get_bin_telemetry("all-stores")
    assert all_stores_res["mode"] == "ALL_LOCATIONS"

    invalid_res = get_bin_telemetry("non-existent-store")
    assert "error" in invalid_res


def test_simulate_sensor_event_invalid():
    """Test simulate_sensor_event error handling."""
    res = simulate_sensor_event(
        store_id="invalid-store", item_key="invalid-item", new_level_percent=5.0
    )
    assert "error" in res


def test_detect_equipment_anomalies_invalid():
    """Test detect_equipment_anomalies with non-existent store."""
    res = detect_equipment_anomalies("non-existent-store")
    assert "error" in res
