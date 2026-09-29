import re

TEMPLATES = {
    "ORDER_CREATED": "Dear {{customer_name}}, your order {{order_number}} has been received by Anand Jewellers. Thank you for choosing us.",
    "ORDER_IN_PROGRESS": "Dear {{customer_name}}, your Anand Jewellers order {{order_number}} is now being crafted in our workshop.",
    "ORDER_READY": "Dear {{customer_name}}, your Anand Jewellers order {{order_number}} is ready for collection. Please contact us if you need any assistance.",
    "ORDER_DELIVERED": "Thank you {{customer_name}} for choosing Anand Jewellers. Order {{order_number}} has been marked as delivered.",
    "ITEM_READY": "Dear {{customer_name}}, your {{item_name}} from order {{order_number}} is ready for collection.",
    "CUSTOM": "{{message}}",
}

_FIELD = re.compile(r"\{\{(\w+)\}\}")


def render(kind: str, **values) -> str:
    template = TEMPLATES.get(kind)
    if template is None:
        raise ValueError("Unknown notification template")
    found = set(_FIELD.findall(template if kind != "CUSTOM" else values.get("message", "")))
    source = values.get("message", "") if kind == "CUSTOM" else template
    if kind == "CUSTOM":
        found = set(_FIELD.findall(source))
    unknown = found - set(values)
    if unknown:
        raise ValueError("Unknown template field: " + ", ".join(sorted(unknown)))

    def replace(match: re.Match) -> str:
        return str(values.get(match.group(1), ""))

    return _FIELD.sub(replace, source)
