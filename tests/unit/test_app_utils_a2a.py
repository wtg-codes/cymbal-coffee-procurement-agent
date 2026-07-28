# Copyright 2026 Google LLC

from app.app_utils.a2a import _ADK_AGENT_EXECUTOR_EXTENSION_URI, _default_capabilities
from app.app_utils.telemetry import setup_telemetry


def test_default_capabilities():
    """Test _default_capabilities builds valid AgentCapabilities with A2UI extensions."""
    caps = _default_capabilities()
    assert caps.streaming is True
    assert len(caps.extensions) > 0
    uris = [ext.uri for ext in caps.extensions]
    assert _ADK_AGENT_EXECUTOR_EXTENSION_URI in uris


def test_setup_telemetry():
    """Test setup_telemetry executes without throwing errors."""
    setup_telemetry()
