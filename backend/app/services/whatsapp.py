import uuid
import httpx
from app.core.config import settings


async def send_item_ready(phone: str, customer_name: str, order_number: str):
    if not settings.WHATSAPP_ENABLED:
        return {"status": "SENT", "message_id": f"dev-{uuid.uuid4().hex[:12]}"}
    url = f"https://graph.facebook.com/{settings.WHATSAPP_GRAPH_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": settings.WHATSAPP_READY_TEMPLATE_NAME,
            "language": {"code": settings.WHATSAPP_TEMPLATE_LANGUAGE},
            "components": [{"type": "body", "parameters": [
                {"type": "text", "text": customer_name},
                {"type": "text", "text": order_number},
            ]}],
        },
    }
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
    return {"status": "SENT", "message_id": data.get("messages", [{}])[0].get("id")}


def dispatch(notification_type: str, phone: str, customer_name: str, order_number: str):
    """Send through WhatsApp when configured. Otherwise record a development send."""
    if not settings.WHATSAPP_ENABLED:
        return {"status": "SENT", "message_id": f"dev-{uuid.uuid4().hex[:12]}"}
    if notification_type in {"ORDER_READY", "ITEM_READY"}:
        import asyncio
        return asyncio.run(send_item_ready(phone, customer_name, order_number))
    return {"status": "FAILED", "error": "WhatsApp template is not configured for this notification type"}
