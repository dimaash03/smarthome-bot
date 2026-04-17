import asyncio
import logging
import os
import sys
import atexit

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

PID_FILE = "/tmp/smarthome_bot.pid"


def check_single_instance():
    """Гарантує що запущено тільки одну копію бота."""
    if os.path.exists(PID_FILE):
        with open(PID_FILE, "r") as f:
            old_pid = f.read().strip()
        try:
            os.kill(int(old_pid), 0)  # перевіряємо чи процес ще живий
            logger.error(f"❌ Бот вже запущений (PID {old_pid}). Зупиніть його спочатку.")
            sys.exit(1)
        except (ProcessLookupError, ValueError, OSError):
            logger.warning(f"⚠️ Знайдено застарілий PID файл, ігноруємо.")

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(lambda: os.remove(PID_FILE) if os.path.exists(PID_FILE) else None)
    logger.info(f"✅ Single instance lock встановлено (PID {os.getpid()})")


async def main():
    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    logger.info("🚀 SmartHome Pro Support Bot starting...")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    check_single_instance()
    asyncio.run(main())
