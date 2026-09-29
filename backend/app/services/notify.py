from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.customer import Customer
from app.models.order import Order
from app.services.audit import record
from app.services.templates import render
from app.tasks.celery_app import send_whatsapp_task


def queue_notification(db: Session, *, customer: Customer, order: Order, kind: str, user=None, item=None, custom_message: str | None = None) -> Notification:
    if not customer.whatsapp_opt_in:
        raise HTTPException(status_code=400, detail="Customer has not opted in to WhatsApp notifications")
    existing = db.query(Notification).filter(
        Notification.customer_id == customer.id,
        Notification.order_id == order.id,
        Notification.notification_type == kind,
        Notification.status.in_(["QUEUED", "SENT"]),
    )
    if item is not None:
        existing = existing.filter(Notification.order_item_id == item.id)
    if existing.first():
        raise HTTPException(status_code=409, detail="This WhatsApp update was already sent or is waiting to send")
    values = {
        "customer_name": customer.name,
        "order_number": order.order_number,
        "item_name": item.item_type if item else "jewellery",
        "message": custom_message or "",
    }
    try:
        message = render(kind, **values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if kind == "CUSTOM" and not (custom_message or "").strip():
        raise HTTPException(status_code=422, detail="Enter a message")
    note = Notification(
        customer_id=customer.id,
        order_id=order.id,
        order_item_id=item.id if item else None,
        channel="WHATSAPP",
        notification_type=kind,
        message=message,
        status="QUEUED",
    )
    db.add(note)
    db.flush()
    record(db, "notification_queued", "notification", note.id, user, {"type": kind, "order": order.order_number})
    db.commit()
    db.refresh(note)
    try:
        send_whatsapp_task.delay(note.id)
    except Exception:
        note.status = "FAILED"
        note.error = "Could not queue notification"
        record(db, "notification_failed", "notification", note.id, user, {"reason": note.error})
        db.commit()
    return note
