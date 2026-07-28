# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Local A2UI tester server.

Serves the interactive HTML client at / and handles A2A JSON-RPC at /jsonrpc.
Uses the official a2ui SDK (parse_response_to_parts) to parse the agent's
<a2ui-json> tagged output into proper A2UI DataParts — identical to what
Gemini Enterprise receives in production.

Run:
    uv run python local_tester/server.py

Then open: http://localhost:8001
"""

import json
import logging
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

# ---------------------------------------------------------------------------
# Bootstrap: add parent dir to sys.path so we can import app.*
# ---------------------------------------------------------------------------
PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PARENT_DIR)
load_dotenv(os.path.join(PARENT_DIR, ".env"))

# Set env vars before importing anything from app
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "hackathon-y26")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "global")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")

# ---------------------------------------------------------------------------
# Imports that depend on env vars being set
# ---------------------------------------------------------------------------
from a2ui.a2a.parts import parse_response_to_parts  # noqa: E402
from google.adk.artifacts import in_memory_artifact_service  # noqa: E402
from google.adk.memory import in_memory_memory_service  # noqa: E402
from google.adk.runners import Runner  # noqa: E402
from google.adk.sessions import in_memory_session_service  # noqa: E402
from google.genai import types as genai_types  # noqa: E402

from app.a2ui_config import A2UI_VERSION  # noqa: E402
from app.agent import root_agent  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("local_tester")

# ---------------------------------------------------------------------------
# FastAPI app + CORS (same origin serving avoids CORS preflight issues)
# ---------------------------------------------------------------------------
app = FastAPI(title="A2UI Local Tester")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ADK Runner (in-memory services — no Cloud deps needed)
# ---------------------------------------------------------------------------
_session_service = in_memory_session_service.InMemorySessionService()
_artifact_service = in_memory_artifact_service.InMemoryArtifactService()
_memory_service = in_memory_memory_service.InMemoryMemoryService()

runner = Runner(
    app_name=root_agent.name,
    agent=root_agent,
    session_service=_session_service,
    artifact_service=_artifact_service,
    memory_service=_memory_service,
)

THIS_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def get_index() -> FileResponse:
    """Serve the interactive HTML client from the same origin."""
    return FileResponse(os.path.join(THIS_DIR, "index.html"))


@app.get("/.well-known/agent-card.json")
async def get_agent_card() -> dict:
    """Minimal agent card for local testing."""
    return {
        "name": root_agent.name,
        "description": root_agent.description or "Cymbal Coffee local tester",
        "url": "http://localhost:8001/jsonrpc",
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "extensions": [
                {
                    "uri": "https://a2ui.org/a2a-extension/a2ui/v0.8",
                    "description": "A2UI rendering support",
                    "required": False,
                }
            ],
        },
    }


@app.post("/jsonrpc")
async def handle_jsonrpc(request: Request) -> dict:
    """Handle A2A JSON-RPC 2.0 requests (message/send method)."""
    body = await request.json()
    logger.info("→ JSON-RPC %s id=%s", body.get("method"), body.get("id"))

    if body.get("jsonrpc") != "2.0":
        return _error(body.get("id"), -32600, "Invalid Request")

    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    if method == "message/send":
        return await _handle_message_send(params, request_id)

    return _error(request_id, -32601, f"Method not found: {method}")


# ---------------------------------------------------------------------------
# message/send handler
# ---------------------------------------------------------------------------


async def _handle_message_send(params: dict, request_id) -> dict:
    message = params.get("message", {})
    session_id = params.get("session_id", "local_session")

    # Extract raw text query
    query: str = message.get("text", "")

    # Extract userAction from DataPart if present (button clicks)
    user_action = None
    for part in message.get("parts", []):
        mime = part.get("metadata", {}).get("mimeType", "")
        if mime in ("application/json+a2ui", "application/a2ui+json"):
            data = part.get("data", {})
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except Exception:
                    pass
            if isinstance(data, dict) and "userAction" in data:
                user_action = data["userAction"]
                break

    # Get or create session
    session = await runner.session_service.get_session(
        app_name=root_agent.name,
        user_id="local_user",
        session_id=session_id,
    )
    if session is None:
        session = await runner.session_service.create_session(
            app_name=root_agent.name,
            user_id="local_user",
            state={},
            session_id=session_id,
        )

    state: dict = dict(session.state or {})

    # Inject userAction context into session state and override query
    if user_action:
        ctx = user_action.get("context", {})
        if isinstance(ctx, dict):
            for k, v in ctx.items():
                state[k] = v
                if k == "message" and v:
                    query = str(v)
        # Persist updated state
        session.state = state

    # Append non-message state keys to query for context
    state_tokens = [
        f"[State: {k}={v}]" for k, v in state.items() if k != "message"
    ]
    if state_tokens:
        query = f"{query} {' '.join(state_tokens)}"
        logger.info("Query with state: %s", query)

    if not query.strip():
        return _error(None, -32602, "Empty query")

    content = genai_types.Content(role="user", parts=[{"text": query}])

    # Run the agent
    final_text: str = ""
    try:
        async for event in runner.run_async(
            user_id="local_user",
            session_id=session.id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for p in event.content.parts:
                    if hasattr(p, "text") and p.text:
                        final_text += p.text
    except Exception as e:
        logger.exception("Agent run failed")
        return _error(request_id, -32603, f"Agent error: {e}")

    if not final_text:
        return _result(request_id, [{"text": "Agent returned no response."}])

    logger.info("Raw agent output (%d chars):\n%s", len(final_text), final_text[:500])

    # Use official A2UI SDK parser — same code path as production
    a2a_parts = parse_response_to_parts(
        final_text,
        fallback_text=final_text,
        version=A2UI_VERSION,
    )

    # Serialise a2a Parts → JSON-serialisable dicts for the wire format
    wire_parts = []
    for part in a2a_parts:
        root = part.root
        if hasattr(root, "text"):
            wire_parts.append({"text": root.text})
        elif hasattr(root, "data"):
            wire_parts.append(
                {
                    "data": root.data,
                    "metadata": {"mimeType": root.metadata.get("mimeType", "application/json+a2ui")},
                }
            )

    if not wire_parts:
        wire_parts = [{"text": final_text}]

    logger.info("Returning %d wire parts", len(wire_parts))
    return _result(request_id, wire_parts)


# ---------------------------------------------------------------------------
# JSON-RPC helpers
# ---------------------------------------------------------------------------


def _result(request_id, parts: list) -> dict:
    return {
        "jsonrpc": "2.0",
        "result": {"message": {"parts": parts}},
        "id": request_id,
    }


def _error(request_id, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "error": {"code": code, "message": message},
        "id": request_id,
    }


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  A2UI Local Tester")
    print("  Open: http://localhost:8001")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
