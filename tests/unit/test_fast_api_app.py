import os

import pytest

os.environ["GOOGLE_CLOUD_PROJECT"] = "hackathon-y26"
os.environ["GCP_PROJECT"] = "hackathon-y26"

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


def test_dashboard_endpoint():
    """GET / and /dashboard should return HTML dashboard."""
    res1 = client.get("/")
    assert res1.status_code == 200

    res2 = client.get("/dashboard")
    assert res2.status_code == 200


def test_dashboard_api_endpoints():
    """Test dashboard data and simulation API routes."""
    res_data = client.get("/api/dashboard/data")
    assert res_data.status_code == 200
    assert "stores" in res_data.json()

    res_start = client.post(
        "/api/dashboard/simulation/start", json={"duration_minutes": 10}
    )
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "SIMULATION_STARTED"

    res_stop = client.post("/api/dashboard/simulation/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "SIMULATION_STOPPED"

    res_sim = client.post(
        "/api/dashboard/simulate",
        json={
            "store_id": "downtown-flagship",
            "item_key": "dark-roast-beans",
            "level_percent": 10.0,
        },
    )
    assert res_sim.status_code == 200
    assert res_sim.json()["new_level_percent"] == 10.0

    res_po = client.post("/api/dashboard/create-po")
    assert res_po.status_code == 200
    assert res_po.json()["success"] is True

    res_reset = client.post("/api/dashboard/reset")
    assert res_reset.status_code == 200
    assert res_reset.json()["status"] == "reset"


def test_app_title():
    """App title must match the agent name."""
    assert app.title == "cymbal-coffee-procurement-agent"


def test_app_description():
    """App description should reference the agent."""
    assert "cymbal-coffee-procurement-agent" in app.description


@pytest.mark.asyncio
async def test_app_lifespan(monkeypatch):
    """Lifespan should initialize runner and attach A2A routes."""
    monkeypatch.setenv("MOCK_LLM_FOR_TEST", "TRUE")
    from app.fast_api_app import lifespan

    async with lifespan(app):
        assert hasattr(app.state, "runner")
        assert app.state.agent_app_name == "app"
        # Test mock_run_async
        events = []
        async for event in app.state.runner.run_async():
            events.append(event)
        assert len(events) == 1
