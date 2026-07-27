# Cymbal Coffee — Intelligent Procurement & Inventory Automation
## 🎥 Live Gemini Enterprise Demo & Presentation Script

---

## 🔗 Quick Access Demo Links & Resources

| Resource | Link / Details |
| --- | --- |
| **Gemini Enterprise Agent UI** | [Launch Live Agent Chat (`12412823214350426517`)](https://vertexaisearch.cloud.google.com/home/cid/1f20f8ae-0e38-46e8-a86f-2e10fb1c8318/r/agent/12412823214350426517) |
| **Gemini Enterprise Console** | [GE Agents Console](https://console.cloud.google.com/gemini-enterprise/locations/global/engines/cymbal-coffee-roasters-dem_1785169638752/agentic/agents?project=hackathon-y26) |
| **Cloud Run Control Panel Dashboard** | [https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/dashboard](https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/dashboard) |
| **GCP Project ID** | `hackathon-y26` |
| **Reasoning Engine ID** | `projects/922201496337/locations/us-central1/reasoningEngines/7462483824006397952` |
| **Eval Pass Rate** | **100% (5/5 cases passed, mean score 4.40/5.0)** |

---

## 📊 Agent Evaluation & Quality Summary (`agents-cli eval`)

The agent passed 100% of evaluation cases in the evaluation suite:

```text
==================================================
EVALUATION SUMMARY
==================================================
Total Eval Cases : 5
Passed           : 5
Failed           : 0
Pass Rate        : 100.0%

Metrics Summary:
  - safety: 1.00 (5/5 passed)
  - tool_call_match: 1.00 (5/5 passed)
  - custom_response_quality: 4.40 / 5.0

Detailed Results:
  ✓ test_get_telemetry: PASSED
  ✓ test_simulate_sensor: PASSED
  ✓ test_create_po: PASSED
  ✓ test_equipment_anomalies: PASSED
  ✓ test_consumption_analysis: PASSED
```

---

## ⏱️ Demo Presentation Agenda (12 Minutes Total)

1. **Intro & Architecture Overview:** 2–3 min
2. **Interactive IoT Telemetry Simulator Demo:** 2 min
3. **Live Chat Interaction in Gemini Enterprise:** 5 min
4. **Quantified Business Value & Wrap-up:** 2 min

---

## 🎬 Step-by-Step Live Demo Walkthrough

### Phase 1: Cloud Run Control Panel & IoT Simulator (2 Minutes)

1. **Open the Cloud Run Control Panel Dashboard**:
   - Open [https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/dashboard](https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/dashboard) in your browser.
   - Click **▶️ Start 2-Hour Demo Session** to start the synthetic IoT simulation engine.
2. **Inject a Simulated Low-Stock Event**:
   - Click the red button: **🚨 Trigger Critical Bean Stock (12% SF)**.
   - Observe the progress bar drop to 12% with a **CRITICAL** status badge.

---

### Phase 2: Live Gemini Enterprise Chat Demo (5 Minutes)

Open **[Gemini Enterprise Live Chat](https://vertexaisearch.cloud.google.com/home/cid/1f20f8ae-0e38-46e8-a86f-2e10fb1c8318/r/agent/12412823214350426517)** and execute the following 4-step sequence:

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

### Phase 3: Verify Results on Cloud Run Dashboard (1 Minute)

1. Switch back to the [Cloud Run Control Panel Dashboard](https://cymbal-coffee-procurement-dashboard-922201496337.us-central1.run.app/dashboard).
2. Show the **Generated Purchase Orders (POs)** table — `PO-CYMBAL-1001` now appears in real time under the table!

---

## 📈 Quantified Business Value Summary

1. **Zero Rush-Hour Stockouts**: Continuous IoT telemetry and consumption velocity forecasting ensure beans and milk are reordered *before* depletion.
2. **25% Reduction in Inventory Holding Costs**: Reorders are calculated dynamically based on real-time consumption velocity.
3. **10+ Hours/Week Saved per Store Manager**: Managers monitor and approve inventory replenishment straight from Gemini Enterprise without context switching.
