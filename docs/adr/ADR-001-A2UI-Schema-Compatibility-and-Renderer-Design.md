# ADR 001: A2UI Schema Compatibility & Universal Renderer Architecture

## Status
**Accepted**

## Context
The Cymbal Coffee Procurement & Inventory Agent generates dynamic Agent-Driven User Interfaces (A2UI) using Google ADK and Vertex AI Agent Engine. During initial development, schema variances between A2UI SDK v0.8 (nested `{component: {Card: ...}}`), v0.9 (flat `{type: "Card", ...}`), and raw model outputs (flat component arrays `[{id: "...", card: {...}}]`) led to rendering failures and inconsistent UI components.

To serve store managers effectively, the UI must:
1. Provide **instant visual clarity** on telemetry (stock levels, consumption rates, temperature).
2. Use **color-coded urgency badges** (OPTIMAL / WARNING / CRITICAL) to draw attention to high-risk inventory.
3. Offer **one-tap actionable workflows** (Reorder, Anomaly Scan, Velocity Forecast) with pre-filled context parameters.
4. Render seamlessly across all schema variations without throwing exceptions or producing unstyled text.

## Decision
We implement a **Universal A2UI Parser and Renderer Pipeline** in both backend and local tester components:

1. **Parser Resilience (`app/a2ui_config.py`)**:
   - `extract_json_payload` extracts JSON blocks enclosed in `<a2ui-json>`, markdown code blocks, or raw JSON.
   - Automatically wraps flat component arrays `[{...}]` into standard `{a2ui_messages: [...]}` structures.

2. **Component Normalization Pipeline (`local_tester/index.html`)**:
   - `normalizeComponent`: Maps v0.8 nested objects, v0.9 flat objects, and lowercase key-based objects (`{card: {...}}`) into a unified canonical component representation (`{type: "Card", props: {...}}`).
   - `getChildrenList`: Safely resolves child lists from `explicitList` arrays or plain arrays.
   - `getTextString`: Resolves text values from string literals, `literalString` wrappers, data model paths (`path`), or nested text objects.

3. **User Story & Persona Centric Design System**:
   - **Card & Column Layout**: High-contrast dark mode slate background (`#1e293b`) with amber indicator border (`#f59e0b`).
   - **Visual Status Badges**: Automatic highlight regex converting `OPTIMAL` -> green badge, `WARNING` -> amber badge, `CRITICAL/URGENT` -> red glowing alert badge.
   - **Interactive Buttons**: Action buttons carry complete parameter context (`message`, `store_id`, `item_key`, `forecast_hours`) in their `userAction` payload to eliminate multi-turn repetition.

## Consequences
- **Positive**: Complete UI resilience against model output variations; high user satisfaction; seamless test suite pass rate (36/36 unit tests).
- **Maintenance**: The local tester acts as a lightweight reference renderer for frontend integration.
