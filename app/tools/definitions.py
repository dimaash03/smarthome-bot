"""
Визначення інструментів (Tools) для Claude API.
Чиста реалізація без LangChain / LlamaIndex.
"""

TOOLS = [
    {
        "name": "get_client_info",
        "description": (
            "Шукає інформацію про клієнта в базі даних магазину за його email-адресою. "
            "Повертає ім'я клієнта та його статус лояльності (наприклад: Bronze, Silver, Gold, VIP). "
            "Використовуй цей інструмент, коли клієнт надав свій email і потрібно дізнатися його дані."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Email-адреса клієнта. Наприклад: ivan@example.com",
                }
            },
            "required": ["email"],
        },
    },
    {
        "name": "get_order_status",
        "description": (
            "Шукає інформацію про замовлення в базі даних за його номером (order_id). "
            "Повертає поточний статус замовлення та очікувану дату доставки. "
            "Використовуй цей інструмент, коли клієнт запитує про конкретне замовлення."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Номер замовлення. Наприклад: 777, ORD-123 тощо.",
                }
            },
            "required": ["order_id"],
        },
    },
]
