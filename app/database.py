# Copyright 2026 Google LLC

import datetime
import os
import random
import sqlite3
from typing import Any

DB_PATH = os.getenv("DATABASE_PATH", "/tmp/cymbal_coffee.db")

STORES_SEED = [
    {
        "store_id": "downtown-flagship",
        "store_name": "Downtown Flagship (#101)",
        "city": "San Francisco, CA",
        "address": "100 Market St",
        "status": "OPTIMAL",
        "store_manager": "Sarah Jenkins",
        "monthly_budget_usd": 18500.0,
        "month_to_date_spend_usd": 8420.50,
    },
    {
        "store_id": "airport-express",
        "store_name": "SFO Terminal 2 (#102)",
        "city": "San Francisco, CA",
        "address": "SFO Airport Gate 54",
        "status": "WARNING",
        "store_manager": "Alex Rivera",
        "monthly_budget_usd": 22000.0,
        "month_to_date_spend_usd": 12650.00,
    },
    {
        "store_id": "financial-district",
        "store_name": "Financial District (#103)",
        "city": "San Francisco, CA",
        "address": "500 California St",
        "status": "OPTIMAL",
        "store_manager": "Marcus Chen",
        "monthly_budget_usd": 15000.0,
        "month_to_date_spend_usd": 6890.00,
    },
    {
        "store_id": "mission-roastery",
        "store_name": "Mission District Roastery (#104)",
        "city": "San Francisco, CA",
        "address": "2200 Mission St",
        "status": "OPTIMAL",
        "store_manager": "Elena Rostova",
        "monthly_budget_usd": 25000.0,
        "month_to_date_spend_usd": 14120.00,
    },
    {
        "store_id": "union-square",
        "store_name": "Union Square Cafe (#105)",
        "city": "San Francisco, CA",
        "address": "350 Powell St",
        "status": "OPTIMAL",
        "store_manager": "David Vance",
        "monthly_budget_usd": 17500.0,
        "month_to_date_spend_usd": 7940.00,
    },
]

PRODUCTS_SEED = [
    {
        "item_key": "dark-roast-beans",
        "item_name": "Organic Dark Roast Beans",
        "category": "beans",
        "max_capacity_kg": 20.0,
        "hourly_consumption_kg": 1.2,
        "base_temp": 21.5,
        "unit_price_usd": 18.50,
        "supplier_name": "Cymbal Artisan Roasters Direct",
    },
    {
        "item_key": "espresso-blend",
        "item_name": "Signature Espresso Blend",
        "category": "beans",
        "max_capacity_kg": 20.0,
        "hourly_consumption_kg": 1.8,
        "base_temp": 22.0,
        "unit_price_usd": 22.00,
        "supplier_name": "Cymbal Artisan Roasters Direct",
    },
    {
        "item_key": "ethiopian-single-origin",
        "item_name": "Single-Origin Ethiopian Beans",
        "category": "beans",
        "max_capacity_kg": 15.0,
        "hourly_consumption_kg": 0.9,
        "base_temp": 21.0,
        "unit_price_usd": 26.50,
        "supplier_name": "Ethiopia Yirgacheffe Specialty Co.",
    },
    {
        "item_key": "colombian-medium-roast",
        "item_name": "Colombian Medium Roast Beans",
        "category": "beans",
        "max_capacity_kg": 20.0,
        "hourly_consumption_kg": 1.4,
        "base_temp": 21.8,
        "unit_price_usd": 19.80,
        "supplier_name": "Cymbal Artisan Roasters Direct",
    },
    {
        "item_key": "oat-milk",
        "item_name": "Barista Edition Oat Milk",
        "category": "milk",
        "max_capacity_kg": 20.0,
        "hourly_consumption_kg": 2.1,
        "base_temp": 3.8,
        "unit_price_usd": 3.20,
        "supplier_name": "Oatly Commercial Supply",
    },
    {
        "item_key": "whole-milk",
        "item_name": "Organic Whole Milk",
        "category": "milk",
        "max_capacity_kg": 25.0,
        "hourly_consumption_kg": 2.5,
        "base_temp": 3.5,
        "unit_price_usd": 2.80,
        "supplier_name": "Clover Sonoma Dairy",
    },
    {
        "item_key": "almond-milk",
        "item_name": "Artisanal Almond Milk",
        "category": "milk",
        "max_capacity_kg": 15.0,
        "hourly_consumption_kg": 1.1,
        "base_temp": 3.9,
        "unit_price_usd": 3.50,
        "supplier_name": "Califia Farms Direct",
    },
    {
        "item_key": "cold-brew-concentrate",
        "item_name": "Cold Brew Concentrate",
        "category": "concentrate",
        "max_capacity_kg": 30.0,
        "hourly_consumption_kg": 1.9,
        "base_temp": 2.8,
        "unit_price_usd": 14.50,
        "supplier_name": "Cymbal Cold Craft Labs",
    },
    {
        "item_key": "vanilla-syrup",
        "item_name": "Organic Vanilla Syrup",
        "category": "syrup",
        "max_capacity_kg": 10.0,
        "hourly_consumption_kg": 0.5,
        "base_temp": 20.0,
        "unit_price_usd": 12.00,
        "supplier_name": "Monin Gourmet Flavors",
    },
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize database tables and seed initial store & product data if empty."""
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS stores (
            store_id TEXT PRIMARY KEY,
            store_name TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            status TEXT NOT NULL,
            store_manager TEXT,
            monthly_budget_usd REAL,
            month_to_date_spend_usd REAL
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS inventory_items (
            store_id TEXT NOT NULL,
            item_key TEXT NOT NULL,
            item_name TEXT NOT NULL,
            category TEXT NOT NULL,
            bin_id TEXT NOT NULL,
            level_percent REAL NOT NULL,
            current_weight_kg REAL NOT NULL,
            max_capacity_kg REAL NOT NULL,
            temp_celsius REAL NOT NULL,
            pressure_bar REAL NOT NULL,
            status TEXT NOT NULL,
            hourly_consumption_kg REAL NOT NULL,
            unit_price_usd REAL DEFAULT 18.50,
            supplier_name TEXT DEFAULT 'Cymbal Roasters Direct',
            PRIMARY KEY (store_id, item_key),
            FOREIGN KEY (store_id) REFERENCES stores(store_id)
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_number TEXT PRIMARY KEY,
            store_id TEXT NOT NULL,
            supplier TEXT NOT NULL,
            item_name TEXT NOT NULL,
            quantity_kg REAL NOT NULL,
            unit_price_usd REAL DEFAULT 18.50,
            subtotal_usd REAL DEFAULT 0.0,
            tax_usd REAL DEFAULT 0.0,
            shipping_usd REAL DEFAULT 0.0,
            total_cost_usd REAL DEFAULT 0.0,
            urgency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            eta_delivery TEXT NOT NULL,
            notes TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS sensor_telemetry_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL,
            item_key TEXT NOT NULL,
            level_percent REAL NOT NULL,
            event_type TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        """)

        # Check if stores exist
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM stores")
        if cursor.fetchone()["cnt"] == 0:
            for store in STORES_SEED:
                conn.execute(
                    """
                    INSERT INTO stores (
                        store_id, store_name, city, address, status, store_manager, monthly_budget_usd, month_to_date_spend_usd
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        store["store_id"],
                        store["store_name"],
                        store["city"],
                        store["address"],
                        store["status"],
                        store.get("store_manager", "Store Manager"),
                        store.get("monthly_budget_usd", 15000.0),
                        store.get("month_to_date_spend_usd", 7500.0),
                    ),
                )

                # Seed items for each store
                for idx, prod in enumerate(PRODUCTS_SEED, start=1):
                    # Set airport-express dark-roast-beans to warning/critical baseline for demo
                    if store["store_id"] == "airport-express" and prod["item_key"] == "dark-roast-beans":
                        level_pct = 15.0
                        status = "WARNING"
                    elif store["store_id"] == "downtown-flagship" and prod["item_key"] == "dark-roast-beans":
                        level_pct = 82.0
                        status = "OPTIMAL"
                    else:
                        level_pct = round(random.uniform(40.0, 95.0), 1)
                        status = "OPTIMAL"

                    max_cap = prod["max_capacity_kg"]
                    current_wt = round((level_pct / 100.0) * max_cap, 1)
                    bin_prefix = "CONT" if prod["category"] in ("milk", "concentrate") else "BIN"
                    bin_id = f"{bin_prefix}-{store['store_id'].upper()[:4]}-{idx:02d}"

                    conn.execute(
                        """
                        INSERT INTO inventory_items (
                            store_id, item_key, item_name, category, bin_id, level_percent,
                            current_weight_kg, max_capacity_kg, temp_celsius, pressure_bar,
                            status, hourly_consumption_kg, unit_price_usd, supplier_name
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            store["store_id"],
                            prod["item_key"],
                            prod["item_name"],
                            prod["category"],
                            bin_id,
                            level_pct,
                            current_wt,
                            max_cap,
                            prod["base_temp"],
                            1.02,
                            status,
                            prod["hourly_consumption_kg"],
                            prod.get("unit_price_usd", 18.50),
                            prod.get("supplier_name", "Cymbal Roasters Direct"),
                        ),
                    )
        conn.commit()


def randomize_telemetry_jitter():
    """Apply realistic IoT sensor jitter (+/- 0.2% to 1.0%) to simulate live continuous streaming telemetry."""
    with get_connection() as conn:
        items = conn.execute("SELECT store_id, item_key, level_percent, max_capacity_kg, temp_celsius FROM inventory_items").fetchall()
        for row in items:
            store_id = row["store_id"]
            item_key = row["item_key"]
            curr_lvl = row["level_percent"]
            max_cap = row["max_capacity_kg"]
            curr_temp = row["temp_celsius"]

            # Minor random fluctuation
            jitter = round(random.uniform(-0.5, 0.5), 1)
            new_lvl = max(5.0, min(100.0, curr_lvl + jitter))
            new_wt = round((new_lvl / 100.0) * max_cap, 1)

            # Recalculate status
            if new_lvl <= 15.0:
                status = "CRITICAL"
            elif new_lvl <= 30.0:
                status = "WARNING"
            else:
                status = "OPTIMAL"

            temp_jitter = round(random.uniform(-0.1, 0.1), 1)
            new_temp = round(curr_temp + temp_jitter, 1)

            conn.execute(
                """
                UPDATE inventory_items
                SET level_percent = ?, current_weight_kg = ?, status = ?, temp_celsius = ?
                WHERE store_id = ? AND item_key = ?
                """,
                (new_lvl, new_wt, status, new_temp, store_id, item_key),
            )
        conn.commit()


def get_all_stores_telemetry() -> dict[str, dict[str, Any]]:
    """Return dictionary of all stores and their bin telemetry from SQLite DB."""
    randomize_telemetry_jitter()
    with get_connection() as conn:
        stores = conn.execute("SELECT * FROM stores").fetchall()
        result = {}
        for s in stores:
            store_id = s["store_id"]
            items = conn.execute(
                "SELECT * FROM inventory_items WHERE store_id = ?", (store_id,)
            ).fetchall()

            bins = {}
            has_critical = False
            has_warning = False
            store_inventory_value = 0.0

            for item in items:
                k = item["item_key"]
                unit_price = item["unit_price_usd"] if "unit_price_usd" in item.keys() else 18.50
                supplier = item["supplier_name"] if "supplier_name" in item.keys() else "Cymbal Roasters Direct"
                curr_wt = item["current_weight_kg"]
                max_cap = item["max_capacity_kg"]
                bin_value = round(curr_wt * unit_price, 2)
                reorder_qty = round(max_cap - curr_wt, 1)
                reorder_cost = round(reorder_qty * unit_price, 2)
                store_inventory_value += bin_value

                bins[k] = {
                    "item_name": item["item_name"],
                    "category": item["category"],
                    "bin_id": item["bin_id"],
                    "level_percent": item["level_percent"],
                    "current_weight_kg": curr_wt,
                    "max_capacity_kg": max_cap,
                    "unit_price_usd": unit_price,
                    "current_value_usd": bin_value,
                    "reorder_qty_kg": reorder_qty,
                    "reorder_cost_usd": reorder_cost,
                    "supplier_name": supplier,
                    "temp_celsius": item["temp_celsius"],
                    "pressure_bar": item["pressure_bar"],
                    "status": item["status"],
                    "hourly_consumption_kg": item["hourly_consumption_kg"],
                }
                if item["status"] == "CRITICAL":
                    has_critical = True
                elif item["status"] == "WARNING":
                    has_warning = True

            overall_status = "CRITICAL" if has_critical else ("WARNING" if has_warning else "OPTIMAL")

            result[store_id] = {
                "store_name": s["store_name"],
                "city": s["city"],
                "address": s["address"],
                "status": overall_status,
                "store_manager": s["store_manager"] if "store_manager" in s.keys() else "Store Manager",
                "monthly_budget_usd": s["monthly_budget_usd"] if "monthly_budget_usd" in s.keys() else 15000.0,
                "month_to_date_spend_usd": s["month_to_date_spend_usd"] if "month_to_date_spend_usd" in s.keys() else 7500.0,
                "total_inventory_value_usd": round(store_inventory_value, 2),
                "bins": bins,
                "anomalies": [],
            }
        return result


def update_sensor_level(store_id: str, item_key: str, new_level: float) -> dict[str, Any]:
    """Persist sensor update directly in SQLite DB and log event."""
    with get_connection() as conn:
        item = conn.execute(
            "SELECT * FROM inventory_items WHERE store_id = ? AND item_key = ?",
            (store_id, item_key),
        ).fetchone()

        if not item:
            return {"error": f"Item '{item_key}' not found at store '{store_id}'."}

        max_cap = item["max_capacity_kg"]
        new_wt = round((new_level / 100.0) * max_cap, 1)
        status = "CRITICAL" if new_level <= 15.0 else ("WARNING" if new_level <= 30.0 else "OPTIMAL")

        conn.execute(
            """
            UPDATE inventory_items
            SET level_percent = ?, current_weight_kg = ?, status = ?
            WHERE store_id = ? AND item_key = ?
            """,
            (new_level, new_wt, status, store_id, item_key),
        )

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            """
            INSERT INTO sensor_telemetry_logs (store_id, item_key, level_percent, event_type, timestamp)
            VALUES (?, ?, ?, 'IOT_SENSOR_UPDATED', ?)
            """,
            (store_id, item_key, new_level, now_str),
        )
        conn.commit()

        return {
            "event": "IOT_SENSOR_TELEMETRY_UPDATED",
            "store_id": store_id,
            "item_name": item["item_name"],
            "new_level_percent": new_level,
            "current_weight_kg": new_wt,
            "status": status,
        }


def insert_purchase_order(po_data: dict[str, Any]) -> dict[str, Any]:
    """Persist a new Purchase Order into SQLite DB."""
    with get_connection() as conn:
        po_number = po_data.get("po_number") or f"PO-CYMBAL-{random.randint(1000, 9999)}"
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            """
            INSERT OR REPLACE INTO purchase_orders (
                po_number, store_id, supplier, item_name, quantity_kg, urgency, status, created_at, eta_delivery, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                po_number,
                po_data.get("store_id", "downtown-flagship"),
                po_data.get("supplier", "Cymbal Roasters Direct"),
                po_data.get("item_name", "Organic Dark Roast Beans"),
                float(po_data.get("quantity_kg", 40.0)),
                po_data.get("urgency", "EXPEDITED"),
                po_data.get("status", "SUBMITTED_AND_CONFIRMED"),
                created_at,
                po_data.get("eta_delivery", "Tomorrow by 08:00 AM"),
                po_data.get("notes", "Auto-generated by Cymbal Procurement Agent"),
            ),
        )
        conn.commit()

        return {
            "po_number": po_number,
            "store_id": po_data.get("store_id"),
            "supplier": po_data.get("supplier"),
            "item_name": po_data.get("item_name"),
            "quantity_kg": po_data.get("quantity_kg"),
            "status": "SUBMITTED_AND_CONFIRMED",
            "created_at": created_at,
            "eta_delivery": po_data.get("eta_delivery", "Tomorrow by 08:00 AM"),
        }


def get_purchase_orders(store_id: str | None = None) -> list[dict[str, Any]]:
    """Retrieve persisted purchase orders from SQLite DB."""
    with get_connection() as conn:
        if store_id:
            rows = conn.execute("SELECT * FROM purchase_orders WHERE store_id = ? ORDER BY created_at DESC", (store_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM purchase_orders ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]


# Initialize DB automatically on import
init_db()
