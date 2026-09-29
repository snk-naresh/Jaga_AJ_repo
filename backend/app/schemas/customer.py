from datetime import datetime
from pydantic import BaseModel, Field
from .common import ORMModel


class CustomerCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=1, max_length=20)
    alternate_phone: str | None = None
    email: str | None = None
    address: str | None = None
    whatsapp_opt_in: bool = False
    notes: str | None = None


class CustomerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = None
    alternate_phone: str | None = None
    email: str | None = None
    address: str | None = None
    whatsapp_opt_in: bool | None = None
    notes: str | None = None


class CustomerOut(ORMModel):
    id: int
    name: str
    phone: str
    alternate_phone: str | None = None
    email: str | None = None
    address: str | None = None
    whatsapp_opt_in: bool
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CustomerPage(BaseModel):
    items: list[CustomerOut]
    total: int
    page: int
    page_size: int
