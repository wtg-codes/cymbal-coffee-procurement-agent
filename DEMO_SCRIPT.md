# Cymbal Coffee — Intelligent Procurement & Inventory Automation
## 🎥 Gemini Enterprise Presentation & Demo Script

---

## ⏱️ Presentation Timing (12 Minutes Total)

* **Intro & Architecture Setup:** 2–3 min
* **Live Demo Interaction in Gemini Enterprise:** 5 min
* **Business Outcomes & Q/A:** 5 min

---

## 🎬 Step-by-Step Script & Prompt Guide

### 1. Presentation Intro (2–3 Minutes)
> **Presenter:**
> *"Welcome! Today we are showcasing **Intelligent Procurement & Inventory Automation** for Cymbal Coffee, built using Google Cloud's **Agent Development Kit (ADK)** and integrated into **Gemini Enterprise** via the **A2A Protocol** and **A2UI** component framework.*
> 
> *The challenge in retail operations is simple: manual inventory checks cause unexpected stockouts during rush hours, while over-ordering leads to holding costs and stale inventory.*
> 
> *Our solution connects IoT coffee bin sensors to Google Cloud, running an autonomous AI agent through a 6-step loop: **Sense → Stream → Reason → Replenish → Order → Notify**."*

---

### 2. Live Demo Sequence (5 Minutes)

#### Step 1: Sense & Stream (Multi-Store Overview)
* **Prompt to Type in Chat:**
  ```text
  Check the real-time coffee bean inventory levels across all Cymbal Coffee store locations.
  ```
* **Agent Response Highlights:**
  - Invokes `get_bin_telemetry("all")`.
  - Renders a multi-store overview showing San Francisco, SFO Airport, Los Angeles, and Seattle.
  - Flags **Downtown Flagship Store #101** Dark Roast bin as low.

---

#### Step 2: Trigger IoT Sensor Event & Alert
* **Prompt to Type in Chat:**
  ```text
  Simulate an IoT sensor drop for Downtown Dark Roast beans down to 12% capacity.
  ```
* **Agent Response Highlights:**
  - Invokes `simulate_sensor_event("downtown-flagship", "dark-roast-beans", 12.0)`.
  - Triggers a `CRITICAL` threshold alert state for Store #101.
  - Renders the **A2UI CRITICAL TELEMETRY THRESHOLD ALERT** card inside Gemini Enterprise.

---

#### Step 3: Reason & Demand Analytics
* **Prompt to Type in Chat:**
  ```text
  Analyze consumption velocity for Downtown Dark Roast and predict our stockout window.
  ```
* **Agent Response Highlights:**
  - Invokes `analyze_consumption_patterns("downtown-flagship", "dark-roast-beans")`.
  - Calculates a **1.2 kg/hr** peak consumption velocity and predicts a stockout in **~2 hours**.
  - Renders the **A2UI DEMAND VELOCITY & STOCKOUT FORECAST CARD**.

---

#### Step 4: Replenish & Auto-Generate Purchase Order
* **Prompt to Type in Chat:**
  ```text
  Generate an expedited Purchase Order to Cymbal Roasters for 40kg of Dark Roast beans.
  ```
* **Agent Response Highlights:**
  - Invokes `create_purchase_order("downtown-flagship", "dark-roast-beans", 40.0, "EXPEDITED")`.
  - Auto-generates `PO-CYMBAL-1001` ($740.00 total) and routes to Cymbal Artisan Roasters Direct.
  - Renders the **A2UI PURCHASE ORDER APPROVAL CARD** with delivery ETA.

---

#### Step 5: Notify & Equipment Health Diagnostics
* **Prompt to Type in Chat:**
  ```text
  Scan equipment health across all stores and notify store managers and customers.
  ```
* **Agent Response Highlights:**
  - Invokes `detect_equipment_anomalies("all")`, `notify_store_manager()`, and `send_customer_notification()`.
  - Renders the **A2UI PROACTIVE NOTIFICATION & DIAGNOSTIC CARD** confirming manager push alerts and customer app notifications ("Fresh Roast ready in 15 mins").

---

### 3. Business Outcomes & Wrap-Up (5 Minutes)

> **Presenter Conclusion:**
> *"By bringing this ADK agent into Gemini Enterprise via A2A and A2UI:
> 1. **Zero Stockouts:** Real-time replenishment prevents revenue loss.
> 2. **25% Holding Cost Reduction:** Safety stock is calculated dynamically based on demand velocity.
> 3. **10+ Hours/Week Saved per Store Manager:** Operations teams manage 100+ stores straight from Gemini Enterprise chat without manual data entry."*
