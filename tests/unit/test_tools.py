# Copyright 2026 Google LLC

from app.tools import (
    analyze_consumption_patterns,
    create_purchase_order,
    detect_equipment_anomalies,
    get_bin_telemetry,
    notify_store_manager,
    send_customer_notification,
    simulate_sensor_event,
)


def test_get_bin_telemetry():
    res = get_bin_telemetry("downtown-flagship")
    assert "bins" in res


def test_simulate_sensor_event():
    res = simulate_sensor_event("downtown-flagship", "dark-roast-beans", 12.0)
    assert res["new_level_percent"] == 12.0


def test_detect_equipment_anomalies():
    res = detect_equipment_anomalies("downtown-flagship")
    assert "health_status" in res


def test_analyze_consumption_patterns():
    res = analyze_consumption_patterns("downtown-flagship", "dark-roast-beans")
    assert "recommendation" in res


def test_create_purchase_order():
    res = create_purchase_order(
        "downtown-flagship", "dark-roast-beans", 40.0, "EXPEDITED"
    )
    assert res["success"] is True


def test_send_customer_notification():
    res = send_customer_notification("downtown-flagship", "Fresh Roast ready!")
    assert res["success"] is True


def test_notify_store_manager():
    res = notify_store_manager(
        "downtown-flagship", "HIGH", "Reorder Dispatched", "PO created."
    )
    assert res["success"] is True
