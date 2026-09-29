from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.security import current_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.order import Order

router = APIRouter(prefix="/reports", tags=["reports"])


def _range(preset: str, start: date | None, end: date | None) -> tuple[date, date]:
    today = datetime.now(timezone.utc).date()
    if preset == "today":
        return today, today
    if preset == "7d":
        return today - timedelta(days=6), today
    if preset == "30d":
        return today - timedelta(days=29), today
    if preset == "month":
        return today.replace(day=1), today
    if preset == "custom":
        if not start or not end or end < start:
            raise HTTPException(status_code=422, detail="Choose a valid start and end date")
        return start, end
    raise HTTPException(status_code=422, detail="Unknown date range")


@router.get("", summary="Shop reports")
def reports(
    preset: str = "30d",
    start: date | None = None,
    end: date | None = None,
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    begin, finish = _range(preset, start, end)
    start_dt = datetime.combine(begin, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(finish, datetime.max.time(), tzinfo=timezone.utc)
    orders = db.query(Order).filter(Order.created_at >= start_dt, Order.created_at <= end_dt).all()
    by_status = {}
    by_date = {}
    for order in orders:
        by_status[order.status] = by_status.get(order.status, 0) + 1
        key = order.created_at.date().isoformat() if order.created_at else ""
        by_date[key] = by_date.get(key, 0) + 1
    customers = db.query(Customer).filter(Customer.created_at >= start_dt, Customer.created_at <= end_dt).all()
    growth = {}
    for customer in customers:
        key = customer.created_at.date().isoformat() if customer.created_at else ""
        growth[key] = growth.get(key, 0) + 1
    repeat = len(db.query(Order.customer_id).filter(Order.created_at >= start_dt, Order.created_at <= end_dt).group_by(Order.customer_id).having(func.count(Order.id) > 1).all())
    notes = db.query(Notification).filter(Notification.created_at >= start_dt, Notification.created_at <= end_dt).all()
    return {
        "start": begin.isoformat(),
        "end": finish.isoformat(),
        "orders_by_status": by_status,
        "orders_by_date": [{"date": key, "count": by_date[key]} for key in sorted(by_date)],
        "ready_orders": by_status.get("READY", 0),
        "pending_orders": by_status.get("OPEN", 0) + by_status.get("IN_PROGRESS", 0),
        "delivered_orders": by_status.get("DELIVERED", 0),
        "customer_growth": [{"date": key, "count": growth[key]} for key in sorted(growth)],
        "new_customers": len(customers),
        "repeat_customers": repeat,
        "notifications": {
            "sent": sum(1 for note in notes if note.status == "SENT"),
            "queued": sum(1 for note in notes if note.status == "QUEUED"),
            "failed": sum(1 for note in notes if note.status == "FAILED"),
        },
    }
