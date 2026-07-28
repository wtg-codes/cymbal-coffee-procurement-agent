# Copyright 2026 Google LLC

import contextlib
import os
from collections.abc import AsyncIterator

import google.auth
import vertexai
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging
from pydantic import BaseModel

from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback
from app.database import get_all_stores_telemetry, get_purchase_orders
from app.tools.procurement import create_purchase_order
from app.tools.telemetry import (
    get_simulation_status,
    simulate_sensor_event,
    start_simulation,
    stop_simulation,
)

load_dotenv()
if not os.getenv("GOOGLE_CLOUD_PROJECT"):
    os.environ["GOOGLE_CLOUD_PROJECT"] = "hackathon-y26"
if not os.getenv("APP_URL") or "0.0.0.0" in os.environ.get("APP_URL", ""):
    os.environ["APP_URL"] = "https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app"

vertexai.init(
    project=os.getenv("GOOGLE_CLOUD_PROJECT", "hackathon-y26"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "global"),
)

setup_telemetry()
try:
    _, project_id = google.auth.default()
    logging_client = google_cloud_logging.Client()
    logger = logging_client.logger(__name__)
except Exception:
    import logging
    from unittest.mock import MagicMock

    import google.auth.credentials

    mock_creds = MagicMock(spec=google.auth.credentials.Credentials)
    mock_creds.token = "mock-token"
    mock_creds.quota_project_id = None
    google.auth.default = lambda *args, **kwargs: (
        mock_creds,
        os.getenv("GOOGLE_CLOUD_PROJECT", "hackathon-y26"),
    )
    logger = logging.getLogger(__name__)

allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    if os.getenv("MOCK_LLM_FOR_TEST") == "TRUE":
        from google.adk.events import Event
        from google.genai.types import Content, Part

        async def mock_run_async(*args, **kwargs):
            yield Event(
                author="app",
                content=Content(
                    parts=[Part.from_text(text="Mock response for integration test")]
                ),
            )

        runner.run_async = mock_run_async

    app.state.runner = runner

    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )

    # Auto-start the simulation so the backend always has live data on boot
    start_simulation(duration_minutes=120)

    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    gemini_enterprise_app_name="app",
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)

app.title = "cymbal-coffee-procurement-agent"
app.description = "API for interacting with the Agent cymbal-coffee-procurement-agent"


STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


@app.get("/health")
def health_check() -> dict:
    return {"status": "healthy", "service": "cymbal-coffee-procurement-dashboard"}


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard() -> HTMLResponse:
    dashboard_path = os.path.join(STATIC_DIR, "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Cymbal Coffee Dashboard</h1>")


@app.get("/api/dashboard/data")
def get_dashboard_data() -> dict:
    return {
        "stores": get_all_stores_telemetry(),
        "purchase_orders": get_purchase_orders(),
        "simulation": get_simulation_status(),
    }


class StartSimRequest(BaseModel):
    duration_minutes: int = 120


@app.post("/api/dashboard/simulation/start")
def api_start_simulation(req: StartSimRequest | None = None) -> dict:
    if req is None:
        req = StartSimRequest()
    return start_simulation(duration_minutes=req.duration_minutes)


@app.post("/api/dashboard/simulation/stop")
def api_stop_simulation() -> dict:
    return stop_simulation()


class SimulateRequest(BaseModel):
    store_id: str
    item_key: str
    level_percent: float


@app.post("/api/dashboard/simulate")
def api_simulate_sensor(req: SimulateRequest) -> dict:
    return simulate_sensor_event(
        store_id=req.store_id,
        item_key=req.item_key,
        new_level_percent=req.level_percent,
    )


@app.post("/api/dashboard/create-po")
def api_create_po() -> dict:
    return create_purchase_order(
        store_id="downtown-flagship",
        item_key="dark-roast-beans",
        quantity_kg=40.0,
        urgency="EXPEDITED",
    )


@app.post("/api/dashboard/reset")
def api_reset_telemetry() -> dict:
    from app.database import update_sensor_level

    update_sensor_level("downtown-flagship", "dark-roast-beans", 82.0)
    update_sensor_level("airport-express", "dark-roast-beans", 15.0)
    return {"status": "reset"}


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    if hasattr(logger, "log_struct"):
        logger.log_struct(feedback.model_dump(), severity="INFO")
    else:
        logger.info(f"Feedback: {feedback.model_dump()}")
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
