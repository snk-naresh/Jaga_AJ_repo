from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.inventory import InventoryItem


def lock_item(db: Session, item_id: int) -> InventoryItem:
    row = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not row or row.status == "INACTIVE":
        raise HTTPException(status_code=404, detail="Inventory item not found")
    return row


def available(row: InventoryItem) -> int:
    return int(row.quantity) - int(row.reserved_quantity)


def reserve(db: Session, item_id: int, quantity: int) -> InventoryItem:
    if quantity < 1:
        raise HTTPException(status_code=422, detail="Quantity must be at least 1")
    row = lock_item(db, item_id)
    if available(row) < quantity:
        raise HTTPException(status_code=409, detail=f"Not enough stock for {row.sku}")
    row.reserved_quantity = int(row.reserved_quantity) + quantity
    return row


def release(db: Session, item_id: int, quantity: int) -> InventoryItem:
    row = lock_item(db, item_id)
    if int(row.reserved_quantity) < quantity:
        raise HTTPException(status_code=409, detail="Cannot release more stock than is reserved")
    row.reserved_quantity = int(row.reserved_quantity) - quantity
    return row


def consume(db: Session, item_id: int, quantity: int) -> InventoryItem:
    row = lock_item(db, item_id)
    if int(row.reserved_quantity) < quantity or int(row.quantity) < quantity:
        raise HTTPException(status_code=409, detail="Reserved stock is no longer available to deliver")
    row.reserved_quantity = int(row.reserved_quantity) - quantity
    row.quantity = int(row.quantity) - quantity
    return row
