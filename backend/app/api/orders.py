import base64
import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.core.security import current_user, require_roles
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.schemas.order import ItemCreate, ItemStatusUpdate, ItemUpdate, OrderCreate, OrderOut, OrderPage, OrderStatusUpdate
from app.services.audit import record
from app.services.inventory import consume, release, reserve
from app.services.notify import queue_notification
from app.services.phones import normalize_phone
from app.services.present import pack_order
from app.services.storage import presigned, upload
from app.services.workflow import assert_item_transition, assert_order_transition, derive_order_status
import qrcode

router = APIRouter(prefix="/orders", tags=["orders"])
ALLOWED_IMAGES = {"image/jpeg", "image/png", "image/webp"}


def _order_query(db: Session):
    return db.query(Order).options(joinedload(Order.items), joinedload(Order.customer))


def _load(db: Session, order_id: int) -> Order:
    order = _order_query(db).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def _sync_status(order: Order) -> None:
    order.status = derive_order_status(order.items)


def _apply_stock(db: Session, item: OrderItem, previous: str, target: str) -> None:
    if not item.inventory_item_id or item.stock_state != "RESERVED":
        return
    if target == "CANCELLED":
        release(db, item.inventory_item_id, item.quantity)
        item.stock_state = "RELEASED"
    elif target == "DELIVERED":
        consume(db, item.inventory_item_id, item.quantity)
        item.stock_state = "CONSUMED"


def _set_item_status(db: Session, item: OrderItem, target: str, notes: str | None, user) -> None:
    assert_item_transition(item.status, target)
    previous = item.status
    _apply_stock(db, item, previous, target)
    item.status = target
    if notes is not None:
        item.workshop_notes = notes
    if target == "READY":
        item.ready_at = datetime.now(timezone.utc)
    record(db, "item_status_changed", "order_item", item.id, user, {"from": previous, "to": target})


@router.get("", response_model=OrderPage, summary="Search orders")
def list_orders(
    q: str | None = None,
    status: str | None = None,
    customer_id: int | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    expected_from: str | None = None,
    expected_to: str | None = None,
    sort: str = "created_desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    query = db.query(Order).join(Customer)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(Order.order_number.ilike(term), Customer.name.ilike(term), Customer.phone.ilike(term)))
    if status:
        query = query.filter(Order.status == status)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if created_from:
        query = query.filter(Order.created_at >= datetime.fromisoformat(created_from))
    if created_to:
        query = query.filter(Order.created_at <= datetime.fromisoformat(created_to).replace(hour=23, minute=59, second=59))
    if expected_from:
        query = query.filter(Order.expected_delivery_date >= expected_from)
    if expected_to:
        query = query.filter(Order.expected_delivery_date <= expected_to)
    sorts = {
        "created_desc": Order.id.desc(),
        "created_asc": Order.id.asc(),
        "expected": Order.expected_delivery_date.asc(),
        "status": Order.status.asc(),
        "number": Order.order_number.asc(),
    }
    total = query.count()
    ordering = sorts.get(sort, Order.id.desc())
    id_rows = query.with_entities(Order.id).order_by(ordering).offset((page - 1) * page_size).limit(page_size).all()
    ids = [row[0] for row in id_rows]
    rows = _order_query(db).filter(Order.id.in_(ids)).all() if ids else []
    rows.sort(key=lambda order: ids.index(order.id))
    return OrderPage(items=[pack_order(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=OrderOut, summary="Create an order with jewellery items")
def create_order(data: OrderCreate, db: Session = Depends(get_db), user=Depends(current_user)):
    if not data.items:
        raise HTTPException(status_code=422, detail="Add at least one jewellery item")
    if data.customer_id:
        customer = db.get(Customer, data.customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    elif data.new_customer:
        payload = data.new_customer.model_dump()
        payload["phone"] = normalize_phone(payload["phone"], required=True)
        payload["alternate_phone"] = normalize_phone(payload.get("alternate_phone"))
        if db.query(Customer).filter(Customer.phone == payload["phone"]).first():
            raise HTTPException(status_code=409, detail="A customer with this mobile number already exists")
        customer = Customer(**payload)
        db.add(customer)
        db.flush()
        record(db, "customer_created", "customer", customer.id, user, {"name": customer.name})
    else:
        raise HTTPException(status_code=422, detail="Select a customer or enter a new one")
    order = Order(
        order_number=f"ANJ-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        customer_id=customer.id,
        expected_delivery_date=data.expected_delivery_date,
        notes=data.notes,
        status="OPEN",
    )
    db.add(order)
    db.flush()
    for index, item in enumerate(data.items, start=1):
        row = OrderItem(
            order_id=order.id,
            item_code=f"{order.order_number}-{index}",
            item_type=item.item_type,
            description=item.description,
            quantity=item.quantity,
            estimated_value=item.estimated_value,
            expected_date=item.expected_date,
            inventory_item_id=item.inventory_item_id,
            workshop_notes=item.workshop_notes,
            status="PENDING",
            stock_state="NONE",
        )
        if item.inventory_item_id:
            reserve(db, item.inventory_item_id, item.quantity)
            row.stock_state = "RESERVED"
        db.add(row)
    record(db, "order_created", "order", order.id, user, {"order_number": order.order_number, "items": len(data.items)})
    db.commit()
    return pack_order(_load(db, order.id))


@router.get("/{order_id}", response_model=OrderOut, summary="View an order")
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    return pack_order(_load(db, order_id))


@router.post("/{order_id}/items", response_model=OrderOut, summary="Add an item to an order")
def add_item(order_id: int, data: ItemCreate, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    order = _load(db, order_id)
    if order.status in {"DELIVERED", "CANCELLED"}:
        raise HTTPException(status_code=400, detail="This order can no longer take new items")
    row = OrderItem(
        order_id=order.id,
        item_code=f"{order.order_number}-{uuid.uuid4().hex[:5].upper()}",
        item_type=data.item_type,
        description=data.description,
        quantity=data.quantity,
        estimated_value=data.estimated_value,
        expected_date=data.expected_date,
        inventory_item_id=data.inventory_item_id,
        workshop_notes=data.workshop_notes,
        status="PENDING",
    )
    if data.inventory_item_id:
        reserve(db, data.inventory_item_id, data.quantity)
        row.stock_state = "RESERVED"
    db.add(row)
    db.flush()
    _sync_status(order)
    record(db, "order_updated", "order", order.id, user, {"added_item": row.item_code})
    db.commit()
    return pack_order(_load(db, order.id))


@router.patch("/items/{item_id}", response_model=OrderOut, summary="Edit an item")
def edit_item(item_id: int, data: ItemUpdate, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item.status in {"DELIVERED", "CANCELLED"}:
        raise HTTPException(status_code=400, detail="This item can no longer be edited")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    record(db, "order_updated", "order_item", item.id, user, {"fields": list(data.model_dump(exclude_unset=True))})
    db.commit()
    return pack_order(_load(db, item.order_id))


@router.patch("/items/{item_id}/status", response_model=OrderOut, summary="Update item status")
def update_status(item_id: int, data: ItemStatusUpdate, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    order = _load(db, item.order_id)
    _set_item_status(db, item, data.status, data.workshop_notes, user)
    previous = order.status
    _sync_status(order)
    if order.status != previous:
        record(db, "order_status_changed", "order", order.id, user, {"from": previous, "to": order.status})
    if data.status == "READY" and order.customer and order.customer.whatsapp_opt_in:
        try:
            queue_notification(db, customer=order.customer, order=order, kind="ITEM_READY", user=user, item=item)
        except HTTPException:
            db.commit()
    else:
        db.commit()
    return pack_order(_load(db, order.id))


@router.patch("/{order_id}/status", response_model=OrderOut, summary="Update order status")
def update_order_status(order_id: int, data: OrderStatusUpdate, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    order = _load(db, order_id)
    assert_order_transition(order.status, data.status)
    previous = order.status
    target_for_items = {"IN_PROGRESS": "IN_PROGRESS", "READY": "READY", "DELIVERED": "DELIVERED", "CANCELLED": "CANCELLED"}.get(data.status)
    if target_for_items:
        for item in order.items:
            if item.status == "CANCELLED" or item.status == "DELIVERED":
                continue
            if target_for_items == "IN_PROGRESS" and item.status not in {"PENDING", "ORDER_CREATED", "ON_HOLD"}:
                continue
            if target_for_items in {"READY", "DELIVERED", "CANCELLED"} or item.status in {"PENDING", "ORDER_CREATED", "ON_HOLD"}:
                if target_for_items in {step for step in ["IN_PROGRESS", "READY", "DELIVERED", "CANCELLED"]}:
                    try:
                        assert_item_transition(item.status, target_for_items)
                    except HTTPException:
                        continue
                    _set_item_status(db, item, target_for_items, None, user)
    order.status = data.status
    record(db, "order_status_changed", "order", order.id, user, {"from": previous, "to": data.status})
    if data.status in {"READY", "DELIVERED"} and order.customer and order.customer.whatsapp_opt_in:
        kind = "ORDER_READY" if data.status == "READY" else "ORDER_DELIVERED"
        db.commit()
        try:
            queue_notification(db, customer=order.customer, order=order, kind=kind, user=user)
        except HTTPException:
            pass
        return pack_order(_load(db, order.id))
    db.commit()
    return pack_order(_load(db, order.id))


@router.post("/items/{item_id}/photo", summary="Attach a photo to an item")
def upload_photo(item_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if file.content_type not in ALLOWED_IMAGES:
        raise HTTPException(status_code=400, detail="Upload a JPEG, PNG, or WebP image")
    content = file.file.read()
    if len(content) > 5_000_000:
        raise HTTPException(status_code=400, detail="Image must be 5 MB or smaller")
    name = Path(file.filename or "photo").name.replace("..", "")
    key = f"orders/{item.order_id}/items/{item.id}/{uuid.uuid4().hex}-{name}"
    upload(key, io.BytesIO(content), file.content_type)
    item.photo_key = key
    record(db, "order_updated", "order_item", item.id, user, {"photo": True})
    db.commit()
    return {"photo_key": key, "url": presigned(key)}


@router.get("/items/{item_id}/photo-url", summary="Photo link for an item")
def photo_url(item_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"url": presigned(item.photo_key)}


@router.get("/items/{item_id}/qr", summary="QR code for an item")
def qr(item_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    img = qrcode.make(item.item_code)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return {"item_code": item.item_code, "png_base64": base64.b64encode(buf.getvalue()).decode()}


@router.post("/items/{item_id}/notify-ready", summary="Queue a ready WhatsApp message")
def notify_ready(item_id: int, db: Session = Depends(get_db), user=Depends(current_user)):
    item = db.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    order = _load(db, item.order_id)
    note = queue_notification(db, customer=order.customer, order=order, kind="ITEM_READY", user=user, item=item)
    return {"notification_id": note.id, "status": note.status}
