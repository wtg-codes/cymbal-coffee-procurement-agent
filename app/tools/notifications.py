# Copyright 2026 Google LLC

import datetime
from typing import Any

SENT_NOTIFICATIONS = []


def send_customer_notification(
    store_id: str = "downtown-flagship",
    message: str = "Fresh Batch Alert: Organic Dark Roast is brewing now!",
) -> dict[str, Any]:
    record = {
        "notification_id": f"NOTIF-{len(SENT_NOTIFICATIONS) + 501}",
        "message": message,
        "status": "DELIVERED",
    }
    SENT_NOTIFICATIONS.append(record)
    return {"success": True, "notification": record}


def notify_store_manager(
    store_id: str = "downtown-flagship",
    priority: str = "HIGH",
    title: str = "Expedited Reorder Dispatched",
    details: str = "PO created.",
) -> dict[str, Any]:
    record = {
        "alert_id": f"ALERT-MGR-{len(SENT_NOTIFICATIONS) + 901}",
        "priority": priority,
        "title": title,
        "details": details,
        "status": "SENT",
    }
    SENT_NOTIFICATIONS.append(record)
    return {"success": True, "alert": record}
