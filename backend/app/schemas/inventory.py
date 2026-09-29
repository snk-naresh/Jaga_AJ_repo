from datetime import datetime
from pydantic import BaseModel, Field
from .common import ORMModel

CATEGORIES = {"Gold", "Diamond", "Silver", "Platinum", "Other"}


class InventoryIn(BaseModel):
    sku: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=150)
    category: str
    description: str | None = None
    quantity: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=2, ge=0)
    weight: str | None = None
    purity: str | None = None
    price: float | None = Field(default=None, ge=0)


class InventoryUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    description: str | None = None
    low_stock_threshold: int | None = Field(default=None, ge=0)
    status: str | None = None
    weight: str | None = None
    purity: str | None = None
    price: float | None = Field(default=None, ge=0)


class StockAdjust(BaseModel):
    delta: int
    reason: str = Field(min_length=2, max_length=200)


class StockReserve(BaseModel):
    quantity: int = Field(ge=1, le=999)


class InventoryOut(ORMModel):
    id: int
    sku: str
    name: str
    category: str
    description: str | None = None
    quantity: int
    reserved_quantity: int
    available_quantity: int = 0
    low_stock_threshold: int
    low_stock: bool = False
    status: str
    weight: str | None = None
    purity: str | None = None
    price: float | None = None
    image_key: str | None = None
    created_at: datetime | None = None


class InventoryPage(BaseModel):
    items: list[InventoryOut]
    total: int
    page: int
    page_size: int
