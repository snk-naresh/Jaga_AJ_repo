from app.schemas.inventory import InventoryOut
from app.schemas.notify import NotificationOut
from app.schemas.order import ItemOut, OrderOut
from app.services.workflow import next_item_statuses, next_order_statuses


def pack_order(order) -> OrderOut:
    data = OrderOut.model_validate(order)
    customer = getattr(order, "customer", None)
    if customer is not None:
        data.customer_name = customer.name
        data.customer_phone = customer.phone
        data.whatsapp_opt_in = customer.whatsapp_opt_in
    data.allowed_transitions = next_order_statuses(order.status)
    packed_items = []
    for item in order.items:
        row = ItemOut.model_validate(item)
        row.allowed_transitions = next_item_statuses(item.status)
        packed_items.append(row)
    data.items = packed_items
    return data


def pack_inventory(row) -> InventoryOut:
    data = InventoryOut.model_validate(row)
    data.available_quantity = int(row.quantity) - int(row.reserved_quantity)
    data.low_stock = data.available_quantity <= int(row.low_stock_threshold)
    return data


def pack_notification(note, customer=None, order=None) -> NotificationOut:
    data = NotificationOut.model_validate(note)
    if customer is not None:
        data.customer_name = customer.name
    if order is not None:
        data.order_number = order.order_number
    return data
