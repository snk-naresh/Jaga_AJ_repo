from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.core.security import current_user, require_roles
from app.db.session import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer import CustomerCreate, CustomerOut, CustomerPage, CustomerUpdate
from app.services.audit import record
from app.services.phones import is_valid_indian_mobile, normalize_phone
from app.services.present import pack_order

router = APIRouter(prefix="/customers", tags=["customers"])


def _apply(data: dict, customer: Customer) -> None:
    if "phone" in data and data["phone"] is not None:
        data["phone"] = normalize_phone(data["phone"], required=True)
    if "alternate_phone" in data:
        data["alternate_phone"] = normalize_phone(data["alternate_phone"])
    if "email" in data and data["email"]:
        email = data["email"].strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise HTTPException(status_code=422, detail="Enter a valid email address")
        data["email"] = email
    for key, value in data.items():
        setattr(customer, key, value)


@router.get("", response_model=CustomerPage, summary="Search customers")
def list_customers(
    q: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _=Depends(current_user),
):
    query = db.query(Customer)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(Customer.name.ilike(term), Customer.phone.ilike(term), Customer.alternate_phone.ilike(term)))
    total = query.count()
    rows = query.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return CustomerPage(items=rows, total=total, page=page, page_size=page_size)


@router.post("", response_model=CustomerOut, summary="Add a customer")
def create_customer(data: CustomerCreate, db: Session = Depends(get_db), user=Depends(current_user)):
    payload = data.model_dump()
    payload["phone"] = normalize_phone(payload["phone"], required=True)
    payload["alternate_phone"] = normalize_phone(payload.get("alternate_phone"))
    if db.query(Customer).filter(Customer.phone == payload["phone"]).first():
        raise HTTPException(status_code=409, detail="A customer with this mobile number already exists")
    customer = Customer(**payload)
    db.add(customer)
    db.flush()
    record(db, "customer_created", "customer", customer.id, user, {"name": customer.name})
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut, summary="View a customer")
def get_customer(customer_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.get("/{customer_id}/profile", summary="Customer profile with order history")
def customer_profile(customer_id: int, db: Session = Depends(get_db), _=Depends(current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    orders = db.query(Order).options(joinedload(Order.items), joinedload(Order.customer)).filter(Order.customer_id == customer.id).order_by(Order.id.desc()).all()
    packed = [pack_order(order) for order in orders]
    def count(status):
        return sum(1 for order in orders if order.status == status)
    items = [item for order in orders for item in order.items]
    return {
        "customer": CustomerOut.model_validate(customer).model_dump(mode="json"),
        "total_orders": len(orders),
        "open_orders": count("OPEN"),
        "in_progress_orders": count("IN_PROGRESS") + count("PARTIALLY_READY"),
        "ready_orders": count("READY"),
        "completed_orders": count("DELIVERED"),
        "total_items": len(items),
        "orders": [row.model_dump(mode="json") for row in packed],
    }


@router.patch("/{customer_id}", response_model=CustomerOut, summary="Edit a customer")
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db), user=Depends(current_user)):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    payload = data.model_dump(exclude_unset=True)
    previous_phone = customer.phone
    phone_invalid = not is_valid_indian_mobile(previous_phone)
    if user.role != "ADMIN":
        if not phone_invalid or set(payload) != {"phone"}:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    if "phone" in payload and payload["phone"]:
        phone = normalize_phone(payload["phone"], required=True)
        taken = db.query(Customer).filter(Customer.phone == phone, Customer.id != customer.id).first()
        if taken:
            raise HTTPException(status_code=409, detail="A customer with this mobile number already exists")
        payload["phone"] = phone
    _apply(payload, customer)
    record(db, "customer_updated", "customer", customer.id, user, {"fields": list(payload)})
    if phone_invalid and customer.phone != previous_phone:
        record(db, "phone_corrected", "customer", customer.id, user, {
            "username": user.username,
            "role": user.role,
            "customer": customer.name,
            "previous_phone": previous_phone,
            "phone": customer.phone,
        })
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", summary="Remove a customer with no orders")
def delete_customer(customer_id: int, db: Session = Depends(get_db), user=Depends(require_roles("ADMIN"))):
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    if db.query(Order).filter(Order.customer_id == customer.id).first():
        raise HTTPException(status_code=409, detail="This customer has orders and cannot be removed")
    record(db, "customer_deleted", "customer", customer.id, user, {"name": customer.name})
    db.delete(customer)
    db.commit()
    return {"status": "deleted"}
