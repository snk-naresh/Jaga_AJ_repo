from sqlalchemy import String,Text,Date,DateTime,ForeignKey,Integer,Float
from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy.sql import func
from app.db.base import Base
class Order(Base):
    __tablename__='orders'
    id:Mapped[int]=mapped_column(primary_key=True)
    order_number:Mapped[str]=mapped_column(String(40),unique=True,index=True)
    customer_id:Mapped[int]=mapped_column(ForeignKey('customers.id'))
    expected_delivery_date:Mapped[object|None]=mapped_column(Date)
    notes:Mapped[str|None]=mapped_column(Text)
    status:Mapped[str]=mapped_column(String(30),default='OPEN',index=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())
    customer=relationship('Customer',back_populates='orders')
    items=relationship('OrderItem',back_populates='order',cascade='all, delete-orphan')
class OrderItem(Base):
    __tablename__='order_items'
    id:Mapped[int]=mapped_column(primary_key=True)
    order_id:Mapped[int]=mapped_column(ForeignKey('orders.id',ondelete='CASCADE'))
    item_code:Mapped[str]=mapped_column(String(60),unique=True,index=True)
    item_type:Mapped[str]=mapped_column(String(80))
    description:Mapped[str|None]=mapped_column(Text)
    quantity:Mapped[int]=mapped_column(Integer,default=1)
    estimated_value:Mapped[float|None]=mapped_column(Float)
    expected_date:Mapped[object|None]=mapped_column(Date)
    ready_at:Mapped[DateTime|None]=mapped_column(DateTime(timezone=True))
    inventory_item_id:Mapped[int|None]=mapped_column(ForeignKey('inventory_items.id'))
    stock_state:Mapped[str]=mapped_column(String(20),default='NONE')
    status:Mapped[str]=mapped_column(String(30),default='PENDING')
    photo_key:Mapped[str|None]=mapped_column(String(500))
    workshop_notes:Mapped[str|None]=mapped_column(Text)
    created_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now())
    order=relationship('Order',back_populates='items')
