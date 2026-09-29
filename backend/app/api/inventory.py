from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.security import current_user, require_roles
from app.db.session import get_db
from app.models.inventory import InventoryItem
from app.schemas.inventory import CATEGORIES, InventoryIn, InventoryOut, InventoryPage, InventoryUpdate, StockAdjust, StockReserve
from app.services.audit import record
from app.services.inventory import release, reserve
from app.services.present import pack_inventory

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _check_category(value: str | None) -> None:
    if value is not None and value not in CATEGORIES:
        raise HTTPException(status_code=422, detail="Choose a category: Gold, Diamond, Silver, Platinum, or Other")


@router.get("", response_model=InventoryPage, summary="Search inventory")
def list_inventory(
    q: str | None = None,
    category: str | None = None,
    low_stock: bool = False,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    query = db.query(InventoryItem)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(InventoryItem.sku.ilike(term), InventoryItem.name.ilike(term), InventoryItem.category.ilike(term)))
    if category:
        query = query.filter(InventoryItem.category == category)
    if low_stock:
        query = query.filter((InventoryItem.quantity - InventoryItem.reserved_quantity) <= InventoryItem.low_stock_threshold)
    total = query.count()
    rows = query.order_by(InventoryItem.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
    return InventoryPage(items=[pack_inventory(row) for row in rows], total=total, page=page, page_size=page_size)


@router.post("", response_model=InventoryOut, summary="Add inventory")
def create_inventory(data: InventoryIn, db: Session = Depends(get_db), user=Depends(current_user)):
    _check_category(data.category)
    if db.query(InventoryItem).filter(InventoryItem.sku == data.sku.strip()).first():
        raise HTTPException(status_code=409, detail="This SKU already exists")
    row = InventoryItem(**data.model_dump())
    row.sku = data.sku.strip()
    db.add(row)
    db.flush()
    record(db, "inventory_adjusted", "inventory", row.id, user, {"sku": row.sku, "quantity": row.quantity})
    db.commit()
    db.refresh(row)
    return pack_inventory(row)


@router.patch("/{item_id}", response_model=InventoryOut, summary="Edit inventory")
def update_inventory(item_id: int, data: InventoryUpdate, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    row = db.get(InventoryItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    payload = data.model_dump(exclude_unset=True)
    _check_category(payload.get("category"))
    if "status" in payload and payload["status"] not in {"ACTIVE", "INACTIVE"}:
        raise HTTPException(status_code=422, detail="Status must be ACTIVE or INACTIVE")
    for key, value in payload.items():
        setattr(row, key, value)
    record(db, "inventory_adjusted", "inventory", row.id, user, {"fields": list(payload)})
    db.commit()
    db.refresh(row)
    return pack_inventory(row)


@router.post("/{item_id}/adjust", response_model=InventoryOut, summary="Adjust on-hand quantity")
def adjust_stock(item_id: int, data: StockAdjust, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    row = db.query(InventoryItem).filter(InventoryItem.id == item_id).with_for_update().first()
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    updated = int(row.quantity) + data.delta
    if updated < int(row.reserved_quantity) or updated < 0:
        raise HTTPException(status_code=409, detail="Adjustment would make stock negative")
    row.quantity = updated
    record(db, "inventory_adjusted", "inventory", row.id, user, {"delta": data.delta, "reason": data.reason})
    db.commit()
    db.refresh(row)
    return pack_inventory(row)


@router.post("/{item_id}/reserve", response_model=InventoryOut, summary="Reserve stock")
def reserve_stock(item_id: int, data: StockReserve, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    row = reserve(db, item_id, data.quantity)
    record(db, "inventory_adjusted", "inventory", row.id, user, {"reserved": data.quantity})
    db.commit()
    db.refresh(row)
    return pack_inventory(row)


@router.post("/{item_id}/release", response_model=InventoryOut, summary="Release reserved stock")
def release_stock(item_id: int, data: StockReserve, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    row = release(db, item_id, data.quantity)
    record(db, "inventory_adjusted", "inventory", row.id, user, {"released": data.quantity})
    db.commit()
    db.refresh(row)
    return pack_inventory(row)


@router.delete("/{item_id}", summary="Remove unused inventory")
def delete_inventory(item_id: int, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    row = db.get(InventoryItem, item_id)
    if not row:
        raise HTTPException(status_code=404, detail="Inventory item not found")
    if int(row.reserved_quantity) > 0:
        raise HTTPException(status_code=409, detail="Reserved stock cannot be removed")
    record(db, "inventory_adjusted", "inventory", row.id, user, {"deleted": row.sku})
    db.delete(row)
    db.commit()
    return {"status": "deleted"}
