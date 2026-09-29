"""Order and item status rules. Older workshop statuses stay valid."""

PENDING = {"PENDING", "ORDER_CREATED", "ON_HOLD"}
IN_PROGRESS = {"IN_PROGRESS", "SENT_TO_WORKSHOP", "QUALITY_CHECK", "REWORK_REQUIRED"}
READY = {"READY"}
DELIVERED = {"DELIVERED"}
CANCELLED = {"CANCELLED"}

ORDER_GRAPH = {
    "OPEN": ["IN_PROGRESS", "CANCELLED"],
    "IN_PROGRESS": ["READY", "CANCELLED"],
    "PARTIALLY_READY": ["READY", "IN_PROGRESS", "CANCELLED"],
    "READY": ["DELIVERED", "CANCELLED"],
    "DELIVERED": [],
    "CANCELLED": [],
}


def bucket(status: str) -> str:
    if status in IN_PROGRESS:
        return "IN_PROGRESS"
    if status in READY:
        return "READY"
    if status in DELIVERED:
        return "DELIVERED"
    if status in CANCELLED:
        return "CANCELLED"
    return "PENDING"


def next_item_statuses(status: str) -> list[str]:
    group = bucket(status)
    if group == "PENDING":
        return ["IN_PROGRESS", "CANCELLED"]
    if group == "IN_PROGRESS":
        return ["READY", "CANCELLED"]
    if group == "READY":
        return ["DELIVERED", "CANCELLED"]
    return []


def next_order_statuses(status: str) -> list[str]:
    return list(ORDER_GRAPH.get(status, []))


def assert_item_transition(current: str, target: str) -> None:
    from fastapi import HTTPException
    if target not in next_item_statuses(current):
        raise HTTPException(status_code=400, detail=f"Cannot move an item from {current} to {target}")


def assert_order_transition(current: str, target: str) -> None:
    from fastapi import HTTPException
    if target not in next_order_statuses(current):
        raise HTTPException(status_code=400, detail=f"Cannot move an order from {current} to {target}")


def derive_order_status(items) -> str:
    if not items:
        return "OPEN"
    groups = [bucket(item.status) for item in items]
    active = [group for group in groups if group != "CANCELLED"]
    if not active:
        return "CANCELLED"
    if all(group == "DELIVERED" for group in active):
        return "DELIVERED"
    if any(group == "IN_PROGRESS" for group in active):
        return "IN_PROGRESS"
    if all(group in {"READY", "DELIVERED"} for group in active):
        return "READY"
    return "OPEN"
