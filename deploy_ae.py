"""Deploy ADK Agent to Vertex AI Agent Engine with A2A Protocol support."""

import os

import vertexai
from a2a.types import AgentSkill
from dotenv import load_dotenv
from vertexai.preview.reasoning_engines import A2aAgent
from vertexai.preview.reasoning_engines.templates.a2a import create_agent_card

import agent_executor


def deploy():
    load_dotenv()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "hackathon-y26")
    location = os.environ.get("LOCATION", "us-central1")
    storage = os.environ.get(
        "STORAGE_BUCKET", "gs://hackathon-y26-agent-engine-staging"
    )

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=storage,
    )

    agent_skill = AgentSkill(
        id="cymbal_coffee_procurement_agent",
        name="Cymbal Coffee Procurement Agent",
        description=(
            "Automated coffee procurement and inventory agent for Cymbal Coffee Roasters"
            " with A2UI support."
        ),
        tags=["procurement", "inventory", "telemetry", "a2ui"],
        examples=[
            "Check inventory telemetry for SF Flagship store",
            "Simulate coffee bean hopper level drop to 12%",
            "Create a purchase order for Dark Roast beans",
        ],
    )

    pp_agent_card = create_agent_card(
        agent_name="Cymbal Coffee Procurement Agent",
        description="Automated coffee procurement and telemetry agent for Cymbal Coffee Roasters",
        skills=[agent_skill],
    )

    a2a_agent = A2aAgent(
        agent_card=pp_agent_card,
        agent_executor_builder=agent_executor.AdkAgentToA2AExecutor,
    )

    client = vertexai.Client(
        project=project_id,
        location=location,
    )

    config = {
        "display_name": "Cymbal Coffee Procurement Agent (A2UI)",
        "description": "Automated coffee procurement and telemetry agent for Cymbal Coffee Roasters",
        "agent_framework": "google-adk",
        "staging_bucket": storage,
        "requirements": [
            "google-adk==1.28.1",
            "google-cloud-aiplatform[agent_engines,adk]==1.162.0",
            "a2a-sdk==0.3.26",
            "pydantic==2.13.4",
            "cloudpickle==3.1.2",
            "protobuf==6.33.6",
            "jsonschema==4.26.0",
        ],
        "max_instances": 2,
        "extra_packages": [
            "agent_executor.py",
            "app",
        ],
        "env_vars": {
            "GOOGLE_CLOUD_LOCATION": "global",
            "GOOGLE_GENAI_USE_VERTEXAI": "true",
            "NUM_WORKERS": "1",
        },
    }

    print("Deploying agent to Vertex AI Agent Engine...")
    remote_agent = client.agent_engines.create(agent=a2a_agent, config=config)
    print(f"✓ Agent Engine deployment created successfully: {remote_agent.api_resource.name}")
    print(f"Reasoning Engine ID: {remote_agent.api_resource.name.split('/')[-1]}")
    return remote_agent


if __name__ == "__main__":
    deploy()
