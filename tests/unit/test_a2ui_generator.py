# Copyright 2026 Google LLC

from app.a2ui_generator import (
    build_consumption_analysis_card,
    build_equipment_diagnostic_card,
    build_fleet_inventory_card,
    build_po_confirmation_card,
    build_visual_chart_card,
    get_scenario_card,
)


def test_build_cards():
    """Test all card builder functions produce valid A2UI 0.8 wire protocol structures."""
    fleet = build_fleet_inventory_card()
    assert len(fleet) == 2
    assert "beginRendering" in fleet[0]
    assert "surfaceUpdate" in fleet[1]

    po = build_po_confirmation_card()
    assert len(po) == 2

    cons = build_consumption_analysis_card()
    assert len(cons) == 2

    eq = build_equipment_diagnostic_card()
    assert len(eq) == 2

    chart = build_visual_chart_card()
    assert len(chart) == 2


def test_get_scenario_card_matching():
    """Test query intent matching to appropriate scenario card."""
    c_po = get_scenario_card("purchase order created")
    assert c_po[0]["beginRendering"]["surfaceId"] == "po_confirmation"

    c_cons = get_scenario_card("analyze consumption velocity")
    assert c_cons[0]["beginRendering"]["surfaceId"] == "consumption_analysis"

    c_eq = get_scenario_card("run diagnostic check for equipment anomalies")
    assert c_eq[0]["beginRendering"]["surfaceId"] == "equipment_diagnostic"

    c_chart = get_scenario_card("show stock level bar chart")
    assert c_chart[0]["beginRendering"]["surfaceId"] == "visual_chart"

    c_fleet = get_scenario_card("check inventory telemetry")
    assert c_fleet[0]["beginRendering"]["surfaceId"] == "fleet_inventory"
