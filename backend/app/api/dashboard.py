from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from app.core.security import current_user
from app.db.session import get_db
from app.models.customer import Customer
from app.models.dashboard_month import DashboardMonth
from app.models.notification import Notification
from app.models.order import Order, OrderItem
from app.services.present import pack_order
from app.services.workflow import PENDING, IN_PROGRESS, READY

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
IST = ZoneInfo("Asia/Kolkata")


def month_window(month: str) -> tuple[datetime, datetime]:
    try:
        year, mon = (int(part) for part in month.split("-"))
        start = datetime(year, mon, 1, tzinfo=IST)
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="Choose a month as YYYY-MM")
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=IST)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=IST)
    return start, end


def build_month(db: Session, month: str) -> dict:
    start, end = month_window(month)
    today = datetime.now(IST)
    last = end - timedelta(days=1)
    series_end = min(last.date(), today.date()) if start <= today < end else last.date()

    def orders(status):
        return db.query(func.count(Order.id)).filter(Order.created_at >= start, Order.created_at < end, Order.status == status).scalar() or 0

    order_query = db.query(Order).options(joinedload(Order.items), joinedload(Order.customer)).filter(Order.created_at >= start, Order.created_at < end)
    month_orders = order_query.order_by(Order.id.desc()).all()
    order_ids = [order.id for order in month_orders]
    item_query = db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)) if order_ids else None
    pending_items = item_query.filter(OrderItem.status.in_(PENDING | IN_PROGRESS)).count() if item_query is not None else 0
    ready_items = item_query.filter(OrderItem.status.in_(READY)).count() if item_query is not None else 0
    recent_customers = db.query(Customer).filter(Customer.created_at >= start, Customer.created_at < end).order_by(Customer.id.desc()).limit(6).all()
    created = db.query(func.date(Order.created_at), func.count(Order.id)).filter(Order.created_at >= start, Order.created_at < end).group_by(func.date(Order.created_at)).all()
    by_day = {}
    for day, count in created:
        key = day.isoformat()[:10] if hasattr(day, "isoformat") else str(day)[:10]
        by_day[key] = int(count)
    series = []
    day = start.date()
    while day <= series_end:
        series.append({"date": day.isoformat(), "count": int(by_day.get(day.isoformat(), 0))})
        day += timedelta(days=1)
    return {
        "month": month,
        "total_customers": db.query(func.count(Customer.id)).filter(Customer.created_at >= start, Customer.created_at < end).scalar() or 0,
        "total_orders": len(month_orders),
        "open_orders": orders("OPEN"),
        "ready_orders": orders("READY"),
        "delivered_orders": orders("DELIVERED"),
        "pending_items": pending_items,
        "ready_items": ready_items,
        "notifications_queued": db.query(func.count(Notification.id)).filter(Notification.created_at >= start, Notification.created_at < end, Notification.status == "QUEUED").scalar() or 0,
        "notifications_failed": db.query(func.count(Notification.id)).filter(Notification.created_at >= start, Notification.created_at < end, Notification.status == "FAILED").scalar() or 0,
        "recent_orders": [pack_order(order).model_dump(mode="json") for order in month_orders[:8]],
        "recent_customers": [{"id": row.id, "name": row.name, "phone": row.phone, "whatsapp_opt_in": row.whatsapp_opt_in} for row in recent_customers],
        "status_distribution": {status: orders(status) for status in ["OPEN", "IN_PROGRESS", "READY", "DELIVERED", "CANCELLED"]},
        "orders_by_day": series,
        "items_summary": {"pending": pending_items, "ready": ready_items},
    }


def save_month(db: Session, payload: dict) -> datetime:
    now = datetime.now(IST)
    row = db.query(DashboardMonth).filter(DashboardMonth.month == payload["month"]).first()
    if row is None:
        row = DashboardMonth(month=payload["month"], details=payload, saved_at=now)
        db.add(row)
    else:
        row.details = payload
        row.saved_at = now
    db.commit()
    db.refresh(row)
    return row.saved_at


@router.get("", summary="Business dashboard for one month")
def dashboard(month: str | None = Query(default=None, description="YYYY-MM. Defaults to the current month."), db: Session = Depends(get_db), _=Depends(current_user)):
    selected = month or datetime.now(IST).strftime("%Y-%m")
    payload = build_month(db, selected)
    saved_at = save_month(db, payload)
    payload["saved_at"] = saved_at.isoformat()
    return payload
