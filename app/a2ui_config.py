# Copyright 2026 Google LLC

import logging

from a2ui.a2a.extension import get_a2ui_agent_extension
from a2ui.a2a.parts import parse_response_to_parts
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.constants import VERSION_0_9
from a2ui.schema.manager import A2uiSchemaManager

logger = logging.getLogger(__name__)

A2UI_VERSION = VERSION_0_9

schema_manager = A2uiSchemaManager(
    version=A2UI_VERSION,
    catalogs=[
        BasicCatalog.get_config(version=A2UI_VERSION),
    ],
)

ROLE_DESCRIPTION = (
    "You are the Cymbal Coffee Intelligent Procurement & Inventory Agent powered by Google Cloud. "
    "Your primary function is to monitor real-time IoT telemetry from coffee bean bins and milk containers, "
    "analyze consumption velocity, detect stockout risks, automatically create Purchase Orders (POs), "
    "identify equipment anomalies, and notify store managers and customers. "
    "Always assist store managers with concise, actionable intelligence."
)

UI_DESCRIPTION = """\
- When presenting store inventory or IoT telemetry readings, use structured card components with metric badges, fill percentage indicators, and clear status labels (OPTIMAL, WARNING, CRITICAL).
- When a Purchase Order is created or reviewed, present a Purchase Order Card displaying the PO Number, Supplier Name, Item, Quantity (kg), Total Cost, Delivery ETA, and Urgency.
- When equipment anomalies or temperature spikes are detected, present an Alert Card with severity level and recommended technician actions.
- For simple conversational responses or clarifications, use plain text.
"""

a2ui_system_prompt = schema_manager.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
)


def get_a2ui_extensions():
    """Return A2UI extensions for the AgentCard capabilities."""
    return [
        get_a2ui_agent_extension(
            A2UI_VERSION,
            schema_manager.accepts_inline_catalogs,
            schema_manager.supported_catalog_ids,
        ),
    ]


def process_a2ui_response(text: str):
    """Parse model text output into A2A-compatible parts."""
    try:
        parts = parse_response_to_parts(text, schema_manager)
        return parts
    except Exception:
        logger.exception("A2UI response parsing failed")
        return None
