# Copyright 2026 Google LLC

from fastapi.testclient import TestClient

from app.fast_api_app import app

client = TestClient(app)


def test_feedback_endpoint():
    """POST /feedback with valid data should return 200 success."""
    response = client.post("/feedback", json={"score": 5, "text": "good"})
    assert response.status_code == 200
    assert response.json() == {"status": "success"}


def test_feedback_endpoint_minimal():
    """POST /feedback with only required field (score) should succeed."""
    response = client.post("/feedback", json={"score": 3})
    assert response.status_code == 200


def test_feedback_endpoint_invalid():
    """POST /feedback with missing required fields should return 422."""
    response = client.post("/feedback", json={"text": "no score"})
    assert response.status_code == 422


def test_app_title():
    """App title must match the agent name."""
    assert app.title == "cymbal-coffee-procurement-agent"


def test_app_description():
    """App description should reference the agent."""
    assert "cymbal-coffee-procurement-agent" in app.description
