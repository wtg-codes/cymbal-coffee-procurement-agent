# Cymbal Coffee - Intelligent Procurement & Inventory Automation Agent

[![ADK Agent](https://img.shields.io/badge/Google-ADK%20Agent-blue)](https://adk.dev/)
[![A2A Protocol](https://img.shields.io/badge/Protocol-A2A-green)](https://a2a-protocol.org/)
[![A2UI Enabled](https://img.shields.io/badge/A2UI-Enabled-orange)](https://github.com/a2ui-project/a2ui)

An autonomous AI Agent built on **Google Agent Development Kit (ADK)** for **Cymbal Coffee Shop Demo**. Demonstrates real-time IoT inventory telemetry, consumption velocity forecasting, automated Purchase Order creation, equipment anomaly detection, A2UI visual cards, and A2A integration registered with **Gemini Enterprise**.

## Project Structure

```
cymbal-coffee-procurement-agent/
├── app/                       # Core agent code
│   ├── agent.py               # Main agent definition (root_agent + App)
│   ├── a2ui_config.py         # A2UI schema manager, prompt builder, post-processing
│   ├── fast_api_app.py        # FastAPI backend server (ADK + A2A routes)
│   ├── app_utils/             # App utilities and helpers
│   │   ├── a2a.py             # A2A route attachment (agent card + JSON-RPC)
│   │   ├── services.py        # Session/artifact service factories
│   │   ├── telemetry.py       # OpenTelemetry setup (Cloud Trace, Logging)
│   │   └── typing.py          # Pydantic models (Feedback, etc.)
│   └── tools/                 # Agent tool implementations
│       ├── telemetry.py       # IoT bin telemetry, sensor events, anomaly detection
│       ├── procurement.py     # Consumption analysis, purchase order creation
│       └── notifications.py   # Customer and store manager notifications
├── tests/                     # Unit, integration, and eval tests
│   ├── unit/                  # Fast, isolated tests
│   ├── integration/           # Agent stream and E2E server tests
│   └── eval/                  # LLM-as-judge evaluation framework
├── DEMO_SCRIPT.md             # 12-minute presentation and demo guide
├── GEMINI.md                  # AI-assisted development guide
├── Dockerfile                 # Container image for deployment
├── pyproject.toml             # Project dependencies and tool config
└── agents-cli-manifest.yaml   # agents-cli project metadata
```

> 💡 **Tip:** Use [Antigravity CLI](https://antigravity.google/) for AI-assisted development — project context is pre-configured in `GEMINI.md`.

## Requirements

Before you begin, ensure you have:
- **uv**: Python package manager (used for all dependency management) — [Install](https://docs.astral.sh/uv/getting-started/installation/) ([add packages](https://docs.astral.sh/uv/concepts/dependencies/) with `uv add <package>`)
- **agents-cli**: Agents CLI — Install with `uv tool install google-agents-cli`
- **Google Cloud SDK**: For GCP services — [Install](https://cloud.google.com/sdk/docs/install)

## Quick Start

Install `agents-cli` and its skills if not already installed:

```bash
uvx google-agents-cli setup
```

Install required packages:

```bash
agents-cli install
```

Test the agent with a local web server:

```bash
agents-cli playground
```

You can also use features from the [ADK](https://adk.dev/) CLI with `uv run adk`.

## Commands

| Command              | Description                                                                                 |
| -------------------- | ------------------------------------------------------------------------------------------- |
| `agents-cli install` | Install dependencies using uv                                                               |
| `agents-cli playground` | Launch local development environment                                                     |
| `agents-cli lint`    | Run code quality checks                                                                     |
| `agents-cli eval`    | Evaluate agent behavior (generate, grade, analyze — see `agents-cli eval --help`)           |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests                                        |
| [A2A Inspector](https://github.com/a2aproject/a2a-inspector) | Launch A2A Protocol Inspector                            |

## 🛠️ Project Management

| Command | What It Does |
|---------|--------------|
| `agents-cli scaffold enhance` | Add CI/CD pipelines and Terraform infrastructure |
| `agents-cli infra cicd` | One-command setup of entire CI/CD pipeline + infrastructure |
| `agents-cli scaffold upgrade` | Auto-upgrade to latest version while preserving customizations |

---

## Development

Edit your agent logic in `app/agent.py` and test with `agents-cli playground` — it auto-reloads on save.

For the demo walkthrough, see [DEMO_SCRIPT.md](DEMO_SCRIPT.md).

## Deployment

```bash
gcloud config set project <your-project-id>
agents-cli deploy
```

To add CI/CD and Terraform, run `agents-cli scaffold enhance`.
To set up your production infrastructure, run `agents-cli infra cicd`.

## Observability

Built-in telemetry exports to Cloud Trace, BigQuery, and Cloud Logging.

## A2A Inspector

This agent supports the [A2A Protocol](https://a2a-protocol.org/). Use the [A2A Inspector](https://github.com/a2aproject/a2a-inspector) to test interoperability.
See the [A2A Inspector docs](https://github.com/a2aproject/a2a-inspector) for details.
