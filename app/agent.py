# ruff: noqa
# Copyright 2026 Google LLC

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

from app.a2ui_config import a2ui_system_prompt
from app.tools import (
    get_bin_telemetry,
    simulate_sensor_event,
    detect_equipment_anomalies,
    analyze_consumption_patterns,
    create_purchase_order,
    send_customer_notification,
    notify_store_manager,
)


root_agent = Agent(
    name="cymbal_coffee_procurement_agent",
    description="Intelligent procurement and inventory agent for Cymbal Coffee Roasters.",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=a2ui_system_prompt,
    tools=[
        get_bin_telemetry,
        simulate_sensor_event,
        detect_equipment_anomalies,
        analyze_consumption_patterns,
        create_purchase_order,
        send_customer_notification,
        notify_store_manager,
    ],
)

app = App(
    root_agent=root_agent,
    name="app",
)
