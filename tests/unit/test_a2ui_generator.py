# Copyright 2026 Google LLC

from app.a2ui_config import (
    convert_v09_messages_to_v08,
    validate_a2ui_messages,
    validate_a2ui_v08_messages,
)
from app.a2ui_generator import (
    build_consumption_analysis_card,
    build_delivery_tracking_card,
    build_equipment_diagnostic_card,
    build_fleet_inventory_card,
    build_notification_confirmed_card,
    build_po_confirmation_card,
    build_visual_chart_card,
    get_scenario_card,
)


def test_build_cards():
    """All card builders must produce schema-valid A2UI v0.9 wire messages."""
    cards = [
        build_fleet_inventory_card(),
        build_po_confirmation_card(),
        build_consumption_analysis_card(),
        build_equipment_diagnostic_card(),
        build_visual_chart_card(),
        build_notification_confirmed_card(),
        build_delivery_tracking_card(),
    ]
    for messages in cards:
        assert len(messages) == 2
        assert "createSurface" in messages[0]
        assert "updateComponents" in messages[1]
        assert messages[1]["updateComponents"]["components"][0]["id"] == "root"
        assert all(
            isinstance(component["component"], str)
            for component in messages[1]["updateComponents"]["components"]
        )
        validate_a2ui_messages(messages)
        v08_messages = convert_v09_messages_to_v08(messages)
        validate_a2ui_v08_messages(v08_messages)
        assert all(
            value.isascii() and "??" not in value
            for value in _text_values(messages) + _text_values(v08_messages)
        )


def _text_values(messages):
    values = []
    for message in messages:
        update = message.get("updateComponents", message.get("surfaceUpdate", {}))
        for component in update.get("components", []):
            definition = component["component"]
            if isinstance(definition, str):
                if definition == "Text":
                    values.append(component["text"])
            elif "Text" in definition:
                values.append(definition["Text"]["text"]["literalString"])
    return values


def test_get_scenario_card_matching():
    """Test query intent matching to appropriate scenario card."""
    # Card 2: PO Confirmed
    c_po = get_scenario_card("purchase order created")
    assert c_po[0]["createSurface"]["surfaceId"] == "po_confirmation"

    # Card 2: PO Confirmed via explicit "PO confirmed" message
    c_po2 = get_scenario_card("Execute expedited PO for 18.8 kg -- PO confirmed")
    assert c_po2[0]["createSurface"]["surfaceId"] == "po_confirmation"

    # Card 3: Consumption Analysis
    c_cons = get_scenario_card("analyze consumption velocity")
    assert c_cons[0]["createSurface"]["surfaceId"] == "consumption_analysis"

    # Card 4: Notification Confirmed
    c_notif = get_scenario_card("notify store manager delivery confirmed")
    assert c_notif[0]["createSurface"]["surfaceId"] == "notification_confirmed"

    # Card 4: Notification Confirmed via "manager notified" text
    c_notif2 = get_scenario_card("manager notified sarah chen")
    assert c_notif2[0]["createSurface"]["surfaceId"] == "notification_confirmed"

    # Card 5: Delivery Tracking
    c_track = get_scenario_card("track delivery for PO-CYMBAL-8297")
    assert c_track[0]["createSurface"]["surfaceId"] == "delivery_tracking"

    # Card 5: Delivery Tracking via "in transit"
    c_track2 = get_scenario_card("order is in transit carrier Pacific Express")
    assert c_track2[0]["createSurface"]["surfaceId"] == "delivery_tracking"

    # Card 6: Equipment Diagnostic
    c_eq = get_scenario_card("run diagnostic check for equipment anomalies")
    assert c_eq[0]["createSurface"]["surfaceId"] == "equipment_diagnostic"

    # Visual Chart
    c_chart = get_scenario_card("show stock level bar chart")
    assert c_chart[0]["createSurface"]["surfaceId"] == "visual_chart"

    # Card 1: Fleet Inventory (default)
    c_fleet = get_scenario_card("check inventory telemetry")
    assert c_fleet[0]["createSurface"]["surfaceId"] == "fleet_inventory"


def test_notification_confirmed_card_content():
    """Notification confirmed card must contain manager name and PO number."""
    messages = build_notification_confirmed_card(
        store="SFO Terminal 2",
        manager="Alex Kim",
        po_num="PO-TEST-0001",
        items_flagged="Organic Dark Roast (14.1%)",
        eta="1 hour",
    )
    assert messages[0]["createSurface"]["surfaceId"] == "notification_confirmed"
    texts = _text_values(messages)
    assert any("Store Manager Notified" in t for t in texts)
    assert any("Alex Kim" in t for t in texts)
    assert any("PO-TEST-0001" in t for t in texts)


def test_delivery_tracking_card_content():
    """Delivery tracking card must contain PO number, carrier, and driver."""
    messages = build_delivery_tracking_card(
        po_num="PO-TEST-9999",
        store="Airport Express",
        carrier="Bay Area Couriers",
        driver="Rosa L.",
        eta="11:00 AM (5 min away)",
        item="Organic Dark Roast Beans",
    )
    assert messages[0]["createSurface"]["surfaceId"] == "delivery_tracking"
    texts = _text_values(messages)
    assert any("Delivery Tracking" in t for t in texts)
    assert any("PO-TEST-9999" in t for t in texts)
    assert any("Bay Area Couriers" in t for t in texts)
    assert any("Rosa L." in t for t in texts)


def test_fleet_card_buttons_flow_forward():
    """Fleet card buttons must point to PO confirmed and consumption, not fleet."""
    messages = build_fleet_inventory_card()
    v08 = convert_v09_messages_to_v08(messages)
    button_messages = [
        comp["component"]["Button"]["action"]["context"]
        for msg in v08
        for comp in msg.get("surfaceUpdate", {}).get("components", [])
        if "Button" in comp.get("component", {})
    ]
    # Flatten context values
    all_action_texts = [
        item["value"]["literalString"]
        for ctx in button_messages
        for item in ctx
        if item.get("key") == "message"
    ]
    # Fleet card should NOT loop back to fleet — it should mention PO or consumption
    assert any("PO confirmed" in t or "consumption" in t.lower() or "analyze" in t.lower() for t in all_action_texts)
    assert not any("check current bean and milk inventory" in t.lower() for t in all_action_texts)


def test_po_card_buttons_flow_forward():
    """PO confirmation card buttons must point to delivery tracking and notification, not back to PO."""
    messages = build_po_confirmation_card()
    v08 = convert_v09_messages_to_v08(messages)
    all_action_texts = [
        item["value"]["literalString"]
        for msg in v08
        for comp in msg.get("surfaceUpdate", {}).get("components", [])
        if "Button" in comp.get("component", {})
        for item in comp["component"]["Button"]["action"]["context"]
        if item.get("key") == "message"
    ]
    assert any("Track delivery" in t or "track" in t.lower() for t in all_action_texts)
    assert any("Notify store manager" in t or "notify" in t.lower() for t in all_action_texts)
    # Must NOT loop back to creating another PO
    assert not any("PO confirmed" in t for t in all_action_texts)
