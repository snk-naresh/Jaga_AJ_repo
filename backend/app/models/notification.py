from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy.sql import func
from app.db.base import Base
class Notification(Base):
    __tablename__='notifications'
    id:Mapped[int]=mapped_column(primary_key=True)
    customer_id:Mapped[int]=mapped_column(ForeignKey('customers.id'))
    order_id:Mapped[int|None]=mapped_column(ForeignKey('orders.id'))
    order_item_id:Mapped[int|None]=mapped_column(ForeignKey('order_items.id'))
    channel:Mapped[str]=mapped_column(String(30))
    notification_type:Mapped[str]=mapped_column(String(40),default='ITEM_READY')
    message:Mapped[str|None]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(30),default='QUEUED',index=True)
    provider_message_id:Mapped[str|None]=mapped_column(String(255))
    error:Mapped[str|None]=mapped_column(Text)
    retry_count:Mapped[int]=mapped_column(Integer,default=0)
    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    sent_at:Mapped[DateTime|None]=mapped_column(DateTime(timezone=True))
