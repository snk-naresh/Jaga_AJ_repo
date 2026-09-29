from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import current_user, require_roles
from app.db.session import get_db
from app.models.customer import Customer
from app.models.notification import Notification
from app.models.order import Order, OrderItem
from app.schemas.notify import NotificationCreate, NotificationPage
from app.services.notify import queue_notification
from app.services.present import pack_notification
from app.tasks.celery_app import send_whatsapp_task

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationPage, summary="Notification history")
def list_notifications(
    status: str | None = None,
    customer_id: int | None = None,
    order_id: int | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    query = db.query(Notification)
    if status:
        query = query.filter(Notification.status == status)
    if customer_id:
        query = query.filter(Notification.customer_id == customer_id)
    if order_id:
        query = query.filter(Notification.order_id == order_id)
    if created_from:
        query = query.filter(Notification.created_at >= created_from)
    if created_to:
        query = query.filter(Notification.created_at <= created_to + "T23:59:59")
    total = query.count()
    rows = query.order_by(Notification.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    packed = []
    for note in rows:
        packed.append(pack_notification(note, db.get(Customer, note.customer_id), db.get(Order, note.order_id) if note.order_id else None))
    return NotificationPage(items=packed, total=total, page=page, page_size=page_size)


@router.post("", summary="Queue a customer notification")
def create_notification(data: NotificationCreate, db: Session = Depends(get_db), user=Depends(current_user)):
    order = db.get(Order, data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    customer = db.get(Customer, order.customer_id)
    item = db.get(OrderItem, data.item_id) if data.item_id else None
    if data.item_id and (not item or item.order_id != order.id):
        raise HTTPException(status_code=404, detail="Item not found on this order")
    if data.kind not in {"ORDER_CREATED", "ORDER_IN_PROGRESS", "ORDER_READY", "ORDER_DELIVERED", "ITEM_READY", "CUSTOM"}:
        raise HTTPException(status_code=422, detail="Unknown notification type")
    note = queue_notification(db, customer=customer, order=order, kind=data.kind, user=user, item=item, custom_message=data.message)
    return pack_notification(note, customer, order)


@router.post("/{notification_id}/retry", summary="Retry a failed notification")
def retry_notification(notification_id: int, db: Session = Depends(get_db), _=Depends(require_roles("ADMIN"))):
    note = db.get(Notification, notification_id)
    if not note:
        raise HTTPException(status_code=404, detail="Notification not found")
    if note.status == "SENT":
        return pack_notification(note, db.get(Customer, note.customer_id), db.get(Order, note.order_id) if note.order_id else None)
    if note.status == "QUEUED":
        return pack_notification(note, db.get(Customer, note.customer_id), db.get(Order, note.order_id) if note.order_id else None)
    note.status = "QUEUED"
    note.error = None
    db.commit()
    try:
        send_whatsapp_task.delay(note.id)
    except Exception:
        note.status = "FAILED"
        note.error = "Could not queue notification"
        db.commit()
    db.refresh(note)
    return pack_notification(note, db.get(Customer, note.customer_id), db.get(Order, note.order_id) if note.order_id else None)
