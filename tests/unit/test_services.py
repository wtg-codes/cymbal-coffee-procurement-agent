# Copyright 2026 Google LLC

import os
from unittest import mock

from app.app_utils.services import (
    ARTIFACT_SERVICE_URI,
    SESSION_SERVICE_URI,
    get_artifact_service,
    get_session_service,
)


def test_session_service_uri_constant():
    """Session service URI should use the shared:// scheme."""
    assert SESSION_SERVICE_URI == "shared://session"


def test_artifact_service_uri_constant():
    """Artifact service URI should use the shared:// scheme."""
    assert ARTIFACT_SERVICE_URI == "shared://artifact"


def test_get_session_service_returns_in_memory():
    """Without env vars, get_session_service should return InMemorySessionService."""
    # Clear the cache to test fresh
    get_session_service.cache_clear()
    with mock.patch.dict(os.environ, {}, clear=False):
        # Remove vars that would trigger other backends
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("SESSION_SERVICE_URI", "GOOGLE_CLOUD_AGENT_ENGINE_ID")
        }
        with mock.patch.dict(os.environ, env, clear=True):
            svc = get_session_service()
            assert svc is not None
            assert "InMemory" in type(svc).__name__
    get_session_service.cache_clear()


def test_get_artifact_service_returns_in_memory():
    """Without LOGS_BUCKET_NAME, get_artifact_service should return InMemoryArtifactService."""
    get_artifact_service.cache_clear()
    with mock.patch.dict(os.environ, {}, clear=False):
        env = {k: v for k, v in os.environ.items() if k != "LOGS_BUCKET_NAME"}
        with mock.patch.dict(os.environ, env, clear=True):
            svc = get_artifact_service()
            assert svc is not None
            assert "InMemory" in type(svc).__name__
    get_artifact_service.cache_clear()


def test_get_session_service_is_cached():
    """Repeated calls should return the same instance (functools.cache)."""
    get_session_service.cache_clear()
    svc1 = get_session_service()
    svc2 = get_session_service()
    assert svc1 is svc2
    get_session_service.cache_clear()
