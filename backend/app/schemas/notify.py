from datetime import datetime
from pydantic import BaseModel, Field
from .common import ORMModel


class NotificationCreate(BaseModel):
    order_id: int
    kind: str
    item_id: int | None = None
    message: str | None = Field(default=None, max_length=500)


class NotificationOut(ORMModel):
    id: int
    customer_id: int
    order_id: int | None = None
    order_item_id: int | None = None
    channel: str
    notification_type: str
    message: str | None = None
    status: str
    provider_message_id: str | None = None
    error: str | None = None
    retry_count: int = 0
    created_at: datetime | None = None
    sent_at: datetime | None = None
    customer_name: str | None = None
    order_number: str | None = None


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    page_size: int
