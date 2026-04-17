"""
Виконавець інструментів — диспетчер між Claude та Google Sheets.
"""
import json
import logging
from typing import Any

from app.sheets.client import get_client_info, get_order_status

logger = logging.getLogger(__name__)


def execute_tool(tool_name: str, tool_input: dict) -> Any:
    """
    Виконує інструмент за назвою та повертає результат як рядок JSON.
    """
    logger.info(f"[Tool] Executing: {tool_name}({tool_input})")

    if tool_name == "get_client_info":
        email = tool_input.get("email", "")
        result = get_client_info(email)
    elif tool_name == "get_order_status":
        order_id = tool_input.get("order_id", "")
        result = get_order_status(order_id)
    else:
        result = {"error": f"Невідомий інструмент: {tool_name}"}
        logger.warning(f"[Tool] Unknown tool called: {tool_name}")

    result_str = json.dumps(result, ensure_ascii=False)
    logger.info(f"[Tool] Result: {result_str}")
    return result_str
