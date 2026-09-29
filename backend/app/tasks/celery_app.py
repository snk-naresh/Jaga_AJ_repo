from datetime import datetime, timezone
from celery import Celery
from app.core.config import settings

celery_app = Celery("anand", broker=settings.REDIS_URL, backend=settings.REDIS_URL)


@celery_app.task(name="app.tasks.notifications.send_whatsapp_task")
def send_whatsapp_task(notification_id: int):
    from app.db.session import SessionLocal
    from app.models.notification import Notification
    from app.models.customer import Customer
    from app.models.order import Order
    from app.services.audit import record
    from app.services.whatsapp import dispatch

    db = SessionLocal()
    note = None
    try:
        note = db.get(Notification, notification_id)
        if not note or note.status == "SENT":
            return
        customer = db.get(Customer, note.customer_id)
        order = db.get(Order, note.order_id) if note.order_id else None
        if note.order_item_id and not order:
            from app.models.order import OrderItem
            item = db.get(OrderItem, note.order_item_id)
            order = db.get(Order, item.order_id) if item else None
        note.retry_count = int(note.retry_count or 0) + 1
        result = dispatch(
            note.notification_type or "ITEM_READY",
            customer.phone,
            customer.name,
            order.order_number if order else "",
        )
        if result.get("status") == "FAILED":
            note.status = "FAILED"
            note.error = result.get("error") or "WhatsApp send failed"
            record(db, "notification_failed", "notification", note.id, None, {"reason": note.error})
        else:
            note.status = "SENT"
            note.error = None
            note.provider_message_id = result.get("message_id")
            note.sent_at = datetime.now(timezone.utc)
            record(db, "notification_sent", "notification", note.id, None, {"provider_message_id": note.provider_message_id})
        db.commit()
    except Exception as exc:
        if note is not None:
            note.status = "FAILED"
            note.error = "WhatsApp send failed"
            record(db, "notification_failed", "notification", note.id, None, {"reason": "provider error"})
            db.commit()
    finally:
        db.close()
