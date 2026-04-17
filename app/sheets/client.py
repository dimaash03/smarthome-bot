import logging
import os
from functools import lru_cache
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials

from app.config import settings

# Базова директорія проєкту (де лежить main.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


@lru_cache(maxsize=1)
def get_sheets_client() -> gspread.Client:
    # Спочатку пробуємо шлях як є, потім — відносно кореня проєкту
    sa_file = settings.GOOGLE_SERVICE_ACCOUNT_FILE
    if not os.path.isabs(sa_file):
        sa_file = os.path.join(BASE_DIR, sa_file)
    logger.info(f"[Sheets] Using service account file: {sa_file}")
    creds = Credentials.from_service_account_file(sa_file, scopes=SCOPES)
    return gspread.authorize(creds)


def get_spreadsheet() -> gspread.Spreadsheet:
    client = get_sheets_client()
    return client.open_by_key(settings.GOOGLE_SHEETS_ID)


def get_client_info(email: str) -> dict:
    """
    Шукає клієнта на листі 'Clients' за email.
    Повертає ім'я та статус лояльності або повідомлення про відсутність.
    """
    try:
        logger.info(f"[Sheets] get_client_info: email={email}")
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("Clients")
        records = worksheet.get_all_records()

        email_lower = email.strip().lower()
        for row in records:
            row_email = str(row.get("Email", "")).strip().lower()
            if row_email == email_lower:
                result = {
                    "found": True,
                    "name": row.get("Name", "—"),
                    "loyalty_status": row.get("Status", "—"),
                    "discount_available": row.get("Discount_Available", "—"),
                    "email": row.get("Email", email),
                }
                logger.info(f"[Sheets] Client found: {result}")
                return result

        logger.info(f"[Sheets] Client not found: {email}")
        return {"found": False, "message": f"Клієнта з email '{email}' не знайдено."}

    except gspread.exceptions.WorksheetNotFound:
        logger.error("[Sheets] Worksheet 'Clients' not found")
        return {"found": False, "message": "Помилка: лист 'Clients' не знайдено в таблиці."}
    except Exception as e:
        logger.exception(f"[Sheets] Error in get_client_info: {e}")
        return {"found": False, "message": f"Помилка при зверненні до бази клієнтів: {str(e)}"}


def get_order_status(order_id: str) -> dict:
    """
    Шукає замовлення на листі 'Orders' за order_id.
    Повертає статус та дату доставки або повідомлення про відсутність.
    """
    try:
        logger.info(f"[Sheets] get_order_status: order_id={order_id}")
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("Orders")
        records = worksheet.get_all_records()

        order_id_clean = str(order_id).strip()
        for row in records:
            row_id = str(row.get("Order_ID", "")).strip()
            if row_id == order_id_clean:
                result = {
                    "found": True,
                    "order_id": row.get("Order_ID", order_id),
                    "status": row.get("Status", "—"),
                    "delivery_date": row.get("Delivery_Date", "—"),
                    "client_email": row.get("Client_Email", "—"),
                }
                logger.info(f"[Sheets] Order found: {result}")
                return result

        logger.info(f"[Sheets] Order not found: {order_id}")
        return {"found": False, "message": f"Замовлення №{order_id} не знайдено в системі."}

    except gspread.exceptions.WorksheetNotFound:
        logger.error("[Sheets] Worksheet 'Orders' not found")
        return {"found": False, "message": "Помилка: лист 'Orders' не знайдено в таблиці."}
    except Exception as e:
        logger.exception(f"[Sheets] Error in get_order_status: {e}")
        return {"found": False, "message": f"Помилка при зверненні до бази замовлень: {str(e)}"}
