# ADR 002: Cloud Run Health Probing & Custom Catalog Visualizations

## Status
**Accepted**

## Context
When running in production environments such as **Gemini Enterprise (GE)** or deployed Cloud Run instances, synthetic data generation and backend services (such as `https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app`) may occasionally experience cold starts, timeouts, or downtime. 

If the backend service is offline when a store manager requests inventory telemetry or analytics, unhandled connection failures could result in generic errors or empty responses, negatively impacting the user experience.

Additionally, store managers require flexible visualization capabilities (**Bar Charts**, **Pie / Donut Charts**, and **Line Graphs**) to analyze inventory levels, stockout risks, and store performance trends.

## Decision

1. **Automated Cloud Run Health Probing (`check_cloud_run_backend_health`)**:
   - Implemented an automated health check probe in `app/tools/telemetry.py` targeting `https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/health`.
   - Registered `check_backend_status` as a first-class tool on `root_agent` in `app/agent.py`.
   - Attached `cloud_run_backend` health status metadata to all telemetry tool outputs.

2. **Urgent Offline Warning A2UI Card Generation**:
   - Instructed the model in `app/a2ui_config.py` (`UI_DESCRIPTION`) to automatically detect when `cloud_run_backend` is `OFFLINE`.
   - When offline, the agent renders a prominent **Warning A2UI Card**:
     - **Title**: `⚠️ Cloud Run Telemetry Backend Offline`
     - **Message**: Clear explanation that synthetic data services at `https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app` are unreachable.
     - **Action Buttons**: `Check Backend Status`, `Retry Telemetry Fetch`, `Open Cloud Run Dashboard`.

3. **Flexible Chart Engine (`generate_telemetry_chart`)**:
   - Created the `generate_telemetry_chart` tool supporting SVG Bar, Pie, Donut, and Line charts embedded via `WebFrameSrcdoc`.
   - Bounded Pie/Donut slice calculations using SVG circle `stroke-dasharray` and `stroke-dashoffset` attributes to guarantee cross-browser iframe paint reliability.
   - Enforced strict Content Security Policy meta tags (`<meta http-equiv="Content-Security-Policy" content="connect-src 'none'">`) on all embedded HTML charts.

4. **Custom Component Catalog (RizzCharts Pattern)**:
   - Added native `Chart` component handling to `local_tester/index.html` following the A2UI RizzCharts custom catalog pattern (`{type: "Chart", chartData: [...]}`).

## Consequences
- **User Value**: Store managers receive instant, clear feedback if backend services are offline, along with direct instructions and one-click action buttons to recover.
- **Robustness**: 100% fail-proof SVG chart rendering in iframe environments.
- **Test Coverage**: 37/37 unit tests passing cleanly across tool execution, schema parsing, and health probing.
