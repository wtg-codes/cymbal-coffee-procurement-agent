# ADR-003: Automated CI/CD Deployment via GitHub Actions over Manual Scripting

## Status
Accepted

## Context
Previously, agent deployments to Vertex AI Agent Engine and Cloud Run were initiated manually from developer workstations using local Python scripts (`deploy_ae.py`).

Manual script execution suffered from key operational issues:
1. **Environment Variance**: Local Python virtual environments (`.venv`), SDK dependencies, and environment variables differed between workstations.
2. **Endpoint & Protocol Mismatch**: Local deployment scripts created standalone Reasoning Engine instances that required custom GCP IAM authentication headers, causing `401/403` transport errors when invoked by Gemini Enterprise.
3. **Lack of Audit Trail & Security Risks**: Manual deployments bypassed pull request reviews, automated CI test suites (`pr-checks.yml`), and security credential management.

## Decision
We deprecate manual local deployment script execution (`deploy_ae.py`). We adopt **GitHub Actions CI/CD (`.github/workflows/deploy.yml`)** as the single authoritative deployment pipeline for the Cymbal Coffee Procurement Agent.

### Key Architectural Rules:
1. **Cloud Run A2A Mode as Production Target**: All production deployments build and ship the containerized A2A FastAPI service (`app/fast_api_app.py`) to Google Cloud Run (`cymbal-coffee-procurement-dashboard`).
2. **Automated Integration & Lint Checks**: Code must pass `pr-checks.yml` (`uv run ruff check .` and `uv run pytest --cov=app --cov-fail-under=80`) before PR merge.
3. **Automated Deployment Triggers**: Merges to the `main` branch automatically trigger `.github/workflows/deploy.yml` via Google Cloud authentication (`google-github-actions/auth`).
4. **Automatic Gemini Enterprise Registration**: Following successful Cloud Run deployment, the pipeline automatically registers/updates the agent card (`/a2a/app/.well-known/agent-card.json`) in Gemini Enterprise via `agents-cli publish gemini-enterprise`.
5. **Mandatory ALL_USERS Sharing Scope**: The deployment workflow MUST explicitly enforce `"sharingConfig": { "scope": "ALL_USERS" }` on Discovery Engine agent registrations. Without explicit `ALL_USERS` scope, agents remain hidden from end-user agent pickers and sidebars.
6. **Required CI/CD IAM Roles**: The CI/CD Service Account (`github-actions-sa`) MUST possess `roles/discoveryengine.admin` on project `hackathon-y26` to manage Discovery Engine API registrations without `403 Forbidden` errors.

## Consequences

### Positive:
- **Zero Local Dependency**: Developers no longer require GCP admin deployment permissions on local workstations.
- **Strict Quality Gates**: Prevents breaking changes from being deployed until all 47+ unit and integration tests pass.
- **Auditability**: Every cloud release is linked to an audited Git commit SHA and GitHub Action run log.
- **Gemini Enterprise Reliability**: Guarantees Gemini Enterprise always routes to a verified, public A2A endpoint with full A2UI v0.9 streaming support.

### Negative / Trade-offs:
- Deployments require code to be committed and merged to `main` rather than ad-hoc local testing (local testing is performed using `agents-cli playground` and `local_tester/server.py`).
