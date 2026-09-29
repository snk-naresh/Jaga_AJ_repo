from datetime import date, datetime, timedelta, timezone
from app.db.session import SessionLocal
from app.models.user import User
from app.models.customer import Customer
from app.models.order import Order, OrderItem
from app.models.notification import Notification
from app.models.inventory import InventoryItem
from app.core.security import hash_password

db = SessionLocal()


def user(username, role):
    if not db.query(User).filter(User.username == username).first():
        db.add(User(username=username, password_hash=hash_password("ChangeMe_123!"), role=role))


def customer(name, phone, opt, notes):
    row = db.query(Customer).filter(Customer.phone == phone).first()
    if row:
        return row
    row = Customer(name=name, phone=phone, whatsapp_opt_in=opt, notes=notes, address="Demo showroom area")
    db.add(row)
    db.flush()
    return row


def inventory(sku, name, category, quantity, reserved, threshold, purity):
    row = db.query(InventoryItem).filter(InventoryItem.sku == sku).first()
    if row:
        return row
    row = InventoryItem(sku=sku, name=name, category=category, quantity=quantity, reserved_quantity=reserved, low_stock_threshold=threshold, purity=purity, weight="sample")
    db.add(row)
    db.flush()
    return row


user("admin", "ADMIN")
user("staff", "STAFF")

anita = customer("Anita Sharma", "9000001001", True, "Prefers 22K gold")
rahul = customer("Rahul Kapoor", "9000001002", False, "Workshop kada")
priya = customer("Priya Nair", "9000001003", True, "Collects on weekends")
meera = customer("Meera Iyer", "9000001004", True, "Diamond setting")

chain = inventory("GLD-CH-22", "22K trace chain", "Gold", 8, 1, 2, "22K")
band = inventory("DIA-RG-18", "18K diamond band", "Diamond", 3, 1, 2, "18K")
bangle = inventory("GLD-BG-22", "22K bangle", "Gold", 1, 0, 2, "22K")
ear = inventory("SLV-ER-92", "Silver earrings", "Silver", 12, 0, 3, "92.5")

now = datetime.now(timezone.utc)


def order(number, person, status, expected, items):
    row = db.query(Order).filter(Order.order_number == number).first()
    if row:
        return row
    row = Order(order_number=number, customer_id=person.id, status=status, expected_delivery_date=expected, notes="Demo workshop order", created_at=now - timedelta(days=3))
    db.add(row)
    db.flush()
    for code, item_type, item_status, sku, qty in items:
        stock = "RESERVED" if sku and item_status not in {"DELIVERED", "CANCELLED"} else "NONE"
        db.add(OrderItem(order_id=row.id, item_code=code, item_type=item_type, description="Demo piece", quantity=qty, status=item_status, inventory_item_id=sku, stock_state=stock, expected_date=expected))
    return row


order("ANJ-DEMO-1001", anita, "IN_PROGRESS", date.today() + timedelta(days=10), [
    ("ANJ-DEMO-1001-1", "Chain", "IN_PROGRESS", chain.id, 1),
    ("ANJ-DEMO-1001-2", "Diamond Ring", "PENDING", band.id, 1),
])
ready = order("ANJ-DEMO-1002", priya, "READY", date.today() + timedelta(days=2), [
    ("ANJ-DEMO-1002-1", "Bangle", "READY", None, 1),
    ("ANJ-DEMO-1002-2", "Earring", "READY", None, 1),
])
order("ANJ-DEMO-1003", rahul, "OPEN", date.today() + timedelta(days=20), [
    ("ANJ-DEMO-1003-1", "Pendant", "PENDING", None, 1),
])
order("ANJ-DEMO-1004", meera, "DELIVERED", date.today() - timedelta(days=1), [
    ("ANJ-DEMO-1004-1", "Necklace", "DELIVERED", None, 1),
])


def note(person, order_number, kind, status, message):
    found = db.query(Order).filter(Order.order_number == order_number).first()
    if db.query(Notification).filter(Notification.order_id == found.id, Notification.notification_type == kind, Notification.status == status).first():
        return
    db.add(Notification(customer_id=person.id, order_id=found.id, channel="WHATSAPP", notification_type=kind, message=message, status=status, sent_at=now if status == "SENT" else None, error="Provider timeout" if status == "FAILED" else None, retry_count=1 if status == "FAILED" else 0))


note(priya, "ANJ-DEMO-1002", "ORDER_READY", "SENT", "Dear Priya Nair, your Anand Jewellers order ANJ-DEMO-1002 is ready for collection.")
note(anita, "ANJ-DEMO-1001", "ORDER_CREATED", "QUEUED", "Dear Anita Sharma, your order ANJ-DEMO-1001 has been received by Anand Jewellers.")
note(meera, "ANJ-DEMO-1004", "ORDER_DELIVERED", "FAILED", "Thank you Meera Iyer for choosing Anand Jewellers.")

db.commit()
print("seed complete")
