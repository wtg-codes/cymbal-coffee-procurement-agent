import json
import logging
import os
import sys

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

load_dotenv(os.path.join(parent_dir, ".env"))

from google.adk import runners  # noqa: E402
from google.adk.artifacts import in_memory_artifact_service  # noqa: E402
from google.adk.memory import in_memory_memory_service  # noqa: E402
from google.adk.sessions import in_memory_session_service  # noqa: E402
from google.genai import types as genai_types  # noqa: E402

import app.agent as agent_module  # noqa: E402
from app.a2ui_config import process_a2ui_response  # noqa: E402

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": adk_agent.name}

adk_agent = agent_module.root_agent
runner = runners.Runner(
    app_name=adk_agent.name,
    agent=adk_agent,
    session_service=in_memory_session_service.InMemorySessionService(),
    artifact_service=in_memory_artifact_service.InMemoryArtifactService(),
    memory_service=in_memory_memory_service.InMemoryMemoryService(),
)


@app.get("/.well-known/agent-card.json")
async def get_agent_card():
    return {
        "capabilities": {
            "streaming": False,
            "extensions": [
                {"uri": "https://a2ui.org/a2a-extension/a2ui/v0.8", "required": False}
            ],
        },
        "name": adk_agent.name,
        "url": "/jsonrpc",
        "version": "1.0.0",
    }


@app.get("/")
async def get_index():
    return FileResponse(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    )


@app.post("/jsonrpc")
async def handle_jsonrpc(request: Request):
    body = await request.json()
    logger.info(f"Received JSON-RPC request: {body}")

    if body.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32600, "message": "Invalid Request"},
            "id": body.get("id"),
        }

    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")

    if method == "message/send":
        message = params.get("message", {})
        query = message.get("text", "").lower().strip()

        if "test simple" in query or "test a2ui" in query:
            sample_a2ui = {
                "a2ui_messages": [
                    {"beginRendering": {"surfaceId": "main", "root": "root_card"}},
                    {
                        "surfaceUpdate": {
                            "surfaceId": "main",
                            "components": [
                                {
                                    "id": "root_card",
                                    "component": {"Card": {"child": "root_col"}},
                                },
                                {
                                    "id": "root_col",
                                    "component": {
                                        "Column": {
                                            "children": {
                                                "explicitList": [
                                                    "card_title",
                                                    "card_body",
                                                    "action_btn",
                                                ]
                                            }
                                        }
                                    },
                                },
                                {
                                    "id": "card_title",
                                    "component": {
                                        "Text": {
                                            "text": {
                                                "literalString": "⚡ Simple A2UI Local Test Card"
                                            },
                                            "usageHint": "h1",
                                        }
                                    },
                                },
                                {
                                    "id": "card_body",
                                    "component": {
                                        "Text": {
                                            "text": {
                                                "literalString": "This verifies that A2UI surface rendering, component graph traversal, and A2A JSON-RPC extensions are working correctly!"
                                            },
                                            "usageHint": "body",
                                        }
                                    },
                                },
                                {
                                    "id": "action_btn",
                                    "component": {
                                        "Button": {
                                            "child": "btn_label",
                                            "action": {
                                                "name": "reorder_beans",
                                                "context": [
                                                    {
                                                        "key": "message",
                                                        "value": {
                                                            "literalString": "Reorder 50kg Coffee Beans"
                                                        },
                                                    }
                                                ],
                                            },
                                        }
                                    },
                                },
                                {
                                    "id": "btn_label",
                                    "component": {
                                        "Text": {
                                            "text": {
                                                "literalString": "🛒 Reorder 50kg Beans"
                                            }
                                        }
                                    },
                                },
                            ],
                        }
                    },
                ]
            }
            return {
                "jsonrpc": "2.0",
                "result": {
                    "message": {
                        "parts": [
                            {"text": "Here is the simple A2UI verification card:"},
                            {
                                "data": sample_a2ui,
                                "metadata": {"mimeType": "application/json+a2ui"},
                            },
                        ]
                    }
                },
                "id": request_id,
            }
        parts = message.get("parts", [])
        session_id = params.get("session_id", "local_session")

        user_action = None
        for part in parts:
            if part.get("metadata", {}).get("mimeType") == "application/json+a2ui":
                data = part.get("data")
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except Exception:
                        pass
                if isinstance(data, dict) and "userAction" in data:
                    user_action = data["userAction"]
                    break

        session = await runner.session_service.get_session(
            app_name=adk_agent.name,
            user_id="local_user",
            session_id=session_id,
        )
        if not session:
            session = await runner.session_service.create_session(
                app_name=adk_agent.name,
                user_id="local_user",
                state={},
                session_id=session_id,
            )

        state = session.state if session.state else {}

        if user_action:
            action_context = user_action.get("context", {})
            for key, value in action_context.items():
                state[key] = value
                if key == "message":
                    query = value
            session.state = state

        state_str = " ".join(
            [f"[State: {k}={v}]" for k, v in state.items() if k not in ["message"]]
        )
        if state_str:
            query = f"{query} {state_str}"
            logger.info(f"Injected state into query: {query}")

        content = genai_types.Content(role="user", parts=[{"text": query}])

        final_response_content = None
        async for event in runner.run_async(
            user_id="local_user", session_id=session.id, new_message=content
        ):
            if event.is_final_response():
                if (
                    event.content
                    and event.content.parts
                    and event.content.parts[0].text
                ):
                    final_response_content = "\n".join(
                        [p.text for p in event.content.parts if p.text]
                    )

        if not final_response_content:
            return {
                "jsonrpc": "2.0",
                "result": {"message": {"text": "No response from agent"}},
                "id": request_id,
            }

        # Parse model response using A2UI SDK parser
        logger.info(f"Raw model output:\n{final_response_content[:2000]}")
        parsed_parts = process_a2ui_response(final_response_content)
        logger.info(f"Parsed parts count: {len(parsed_parts)}")
        parts = []
        if parsed_parts:
            for part in parsed_parts:
                if isinstance(part, dict):
                    parts.append(part)
                elif hasattr(part, "root"):
                    root = part.root
                    if hasattr(root, "text"):
                        parts.append({"text": root.text})
                    elif hasattr(root, "data"):
                        parts.append(
                            {
                                "data": root.data,
                                "metadata": {"mimeType": "application/json+a2ui"},
                            }
                        )
        if not parts:
            parts.append({"text": final_response_content})

        return {
            "jsonrpc": "2.0",
            "result": {"message": {"parts": parts}},
            "id": request_id,
        }

    return {
        "jsonrpc": "2.0",
        "error": {"code": -32601, "message": "Method not found"},
        "id": request_id,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
