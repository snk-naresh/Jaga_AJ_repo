from datetime import date, datetime
from pydantic import BaseModel, Field
from .common import ORMModel
from .customer import CustomerCreate


class ItemIn(BaseModel):
    item_type: str = Field(min_length=2, max_length=80)
    description: str | None = None
    quantity: int = Field(default=1, ge=1, le=99)
    expected_date: date | None = None
    estimated_value: float | None = Field(default=None, ge=0)
    inventory_item_id: int | None = None
    workshop_notes: str | None = None


class ItemCreate(ItemIn):
    pass


class ItemUpdate(BaseModel):
    description: str | None = None
    quantity: int | None = Field(default=None, ge=1, le=99)
    expected_date: date | None = None
    estimated_value: float | None = Field(default=None, ge=0)
    workshop_notes: str | None = None


class ItemStatusUpdate(BaseModel):
    status: str
    workshop_notes: str | None = None


class OrderCreate(BaseModel):
    customer_id: int | None = None
    new_customer: CustomerCreate | None = None
    expected_delivery_date: date | None = None
    notes: str | None = None
    items: list[ItemIn] = Field(default_factory=list)


class OrderStatusUpdate(BaseModel):
    status: str


class ItemOut(ORMModel):
    id: int
    item_code: str
    item_type: str
    description: str | None = None
    quantity: int = 1
    estimated_value: float | None = None
    expected_date: date | None = None
    ready_at: datetime | None = None
    inventory_item_id: int | None = None
    stock_state: str = "NONE"
    status: str
    photo_key: str | None = None
    workshop_notes: str | None = None
    allowed_transitions: list[str] = []


class OrderOut(ORMModel):
    id: int
    order_number: str
    customer_id: int
    customer_name: str | None = None
    customer_phone: str | None = None
    whatsapp_opt_in: bool | None = None
    expected_delivery_date: date | None = None
    notes: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    items: list[ItemOut] = []
    allowed_transitions: list[str] = []


class OrderPage(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    page_size: int
