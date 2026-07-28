# Copyright 2026 Google LLC

from app.a2ui_config import (
    convert_v09_messages_to_v08,
    validate_a2ui_messages,
    validate_a2ui_v08_messages,
)
from app.a2ui_generator import (
    build_consumption_analysis_card,
    build_equipment_diagnostic_card,
    build_fleet_inventory_card,
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
    c_po = get_scenario_card("purchase order created")
    assert c_po[0]["createSurface"]["surfaceId"] == "po_confirmation"

    c_cons = get_scenario_card("analyze consumption velocity")
    assert c_cons[0]["createSurface"]["surfaceId"] == "consumption_analysis"

    c_eq = get_scenario_card("run diagnostic check for equipment anomalies")
    assert c_eq[0]["createSurface"]["surfaceId"] == "equipment_diagnostic"

    c_chart = get_scenario_card("show stock level bar chart")
    assert c_chart[0]["createSurface"]["surfaceId"] == "visual_chart"

    c_fleet = get_scenario_card("check inventory telemetry")
    assert c_fleet[0]["createSurface"]["surfaceId"] == "fleet_inventory"
