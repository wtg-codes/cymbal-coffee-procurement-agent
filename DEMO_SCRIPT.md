# Cymbal Coffee — Intelligent Procurement & Inventory Automation
## 🎥 Live Gemini Enterprise Demo & Presentation Script

---

## 🔗 Quick Access Demo Links & Resources

| Resource | Link / Value |
| --- | --- |
| **Gemini Enterprise Agent UI** | [Launch Live Agent Chat](https://vertexaisearch.cloud.google.com/home/cid/1f20f8ae-0e38-46e8-a86f-2e10fb1c8318/r/agent/12078504257893178677) |
| **Gemini Enterprise Console** | [GE Agents Console](https://console.cloud.google.com/gemini-enterprise/locations/global/engines/cymbal-coffee-roasters-dem_1785169638752/agentic/agents?project=hackathon-y26) |
| **Local Control Panel Dashboard** | [http://localhost:8000/dashboard](http://localhost:8000/dashboard) |
| **GCP Project ID** | `hackathon-y26` |
| **Active Reasoning Engine ID** | `projects/922201496337/locations/us-central1/reasoningEngines/7462483824006397952` |
| **GE Registered Agent ID** | `12078504257893178677` |

---

## ⏱️ Demo Presentation Agenda (12 Minutes Total)

1. **Intro & Architecture Overview:** 2–3 min
2. **Interactive IoT Telemetry Simulator Demo:** 2 min
3. **Live Chat Interaction in Gemini Enterprise:** 5 min
4. **Quantified Business Value & Wrap-up:** 2 min

---

## 🎬 Step-by-Step Live Demo Walkthrough

### Phase 1: Local Control Panel & IoT Simulator (2 Minutes)

1. **Launch the Local Server**:
   ```bash
   uv run python -m app.fast_api_app
   ```
2. **Open the Control Panel Dashboard**:
   - Open [http://localhost:8000/dashboard](http://localhost:8000/dashboard) in your browser.
   - **Show the Audience**: Point out the live telemetry bins for *Downtown Flagship (#101)* and *SFO Terminal 2 (#102)*.
3. **Inject a Simulated Low-Stock Event**:
   - Click the red button: **🚨 Trigger Critical Bean Stock (12% SF)**.
   - Observe the progress bar drop to 12% with a **CRITICAL** status badge.

---

### Phase 2: Live Gemini Enterprise Chat Demo (5 Minutes)

Open the **[Live Gemini Enterprise Agent Chat](https://vertexaisearch.cloud.google.com/home/cid/1f20f8ae-0e38-46e8-a86f-2e10fb1c8318/r/agent/12078504257893178677)** and execute the following 4-step sequence:

#### Step 1: Real-time Telemetry Health Check
* **Prompt to Copy & Paste**:
  ```text
  Check current coffee bean and milk inventory telemetry across all store locations and alert me if any levels are critical.
  ```
* **What the Agent Does**:
  - Calls tool `get_bin_telemetry("all")`.
  - Analyzes store levels and identifies **Downtown Flagship Store #101** (Organic Dark Roast Beans at 12% capacity, 2.4kg remaining).
  - Renders an **A2UI Critical Telemetry Threshold Alert Card** displaying store details, temperature, and current stock status.

---

#### Step 2: Demand Velocity & Stockout Forecasting
* **Prompt to Copy & Paste**:
  ```text
  Analyze consumption velocity for Dark Roast Beans at Downtown Flagship and predict our stockout window.
  ```
* **What the Agent Does**:
  - Calls tool `analyze_consumption_patterns("downtown-flagship", "dark-roast-beans")`.
  - Calculates a **1.2 kg/hr** peak consumption rate and estimates a stockout window of **~2 hours**.
  - Recommends an expedited reorder of **40kg**.

---

#### Step 3: Automated Purchase Order Creation & Routing
* **Prompt to Copy & Paste**:
  ```text
  Generate an expedited Purchase Order to Cymbal Roasters for 40kg of Dark Roast beans.
  ```
* **What the Agent Does**:
  - Calls tool `create_purchase_order("downtown-flagship", "dark-roast-beans", 40.0, "EXPEDITED")`.
  - Generates Purchase Order `PO-CYMBAL-1001` ($740.00 total) with a 2-hour delivery ETA.
  - Renders the **A2UI Purchase Order Approval Card** showing item details, supplier name, unit price, and delivery window.

---

#### Step 4: Equipment Anomaly Scan & Operations Notification
* **Prompt to Copy & Paste**:
  ```text
  Scan equipment health across all stores and notify store managers and customers.
  ```
* **What the Agent Does**:
  - Calls tools `detect_equipment_anomalies("all")`, `notify_store_manager()`, and `send_customer_notification()`.
  - Confirms system health and outputs notification confirmation badges for store operations.

---

### Phase 3: Verify Results on Local Dashboard (1 Minute)

1. Switch back to [http://localhost:8000/dashboard](http://localhost:8000/dashboard).
2. Show the **Generated Purchase Orders (POs)** table — `PO-CYMBAL-1001` now appears in real time under the table!

---

## 📈 Quantified Business Value Summary

1. **Zero Rush-Hour Stockouts**: Continuous IoT telemetry and consumption velocity forecasting ensure beans and milk are reordered *before* depletion.
2. **25% Reduction in Inventory Holding Costs**: Reorders are calculated dynamically based on real-time consumption velocity.
3. **10+ Hours/Week Saved per Store Manager**: Managers monitor and approve inventory replenishment straight from Gemini Enterprise without context switching.

---

## 🛠️ Verification & Troubleshooting Commands

```bash
# Run unit & integration test suite
uv run pytest

# Check active GCP authentication
gcloud auth list

# Verify Discovery Engine registered agents
curl -s -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://discoveryengine.googleapis.com/v1alpha/projects/hackathon-y26/locations/global/collections/default_collection/engines/cymbal-coffee-roasters-dem_1785169638752/assistants/default_assistant/agents"
```
