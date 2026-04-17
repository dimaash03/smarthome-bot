"""
Telegram-хендлери (aiogram 3.x).
Обробка /start, повідомлень, typing-індикатора та помилок.
"""
import asyncio
import logging
from collections import defaultdict

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import (
    BotCommand,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)

from app.agent import run_agent

logger = logging.getLogger(__name__)
router = Router()

# Зберігаємо historію розмов per user (in-memory)
# Для продакшну варто замінити на Redis
conversation_histories: dict[int, list] = defaultdict(list)

WELCOME_MESSAGE = """👋 Вітаю! Я — *Макс*, ваш персональний асистент магазину *SmartHome Pro*.

Я можу допомогти вам:
• 📦 Перевірити статус замовлення
• 👤 Знайти інформацію про ваш профіль
• 🕐 Розповісти про графік роботи та контакти

Просто напишіть своє запитання — і я одразу допоможу! 😊

_Для перевірки замовлення вкажіть номер замовлення та ваш email._"""

QUICK_REPLIES = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📦 Статус замовлення"),
            KeyboardButton(text="🕐 Графік роботи"),
        ],
        [
            KeyboardButton(text="📞 Контакти підтримки"),
            KeyboardButton(text="🔄 Очистити історію"),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обробка команди /start."""
    user_id = message.from_user.id
    conversation_histories[user_id].clear()  # скидаємо контекст при /start

    await message.answer(
        WELCOME_MESSAGE,
        parse_mode="Markdown",
        reply_markup=QUICK_REPLIES,
    )
    logger.info(f"[Handler] /start from user_id={user_id}")


@router.message(Command("clear"))
async def cmd_clear(message: Message):
    """Очищення історії розмови."""
    user_id = message.from_user.id
    conversation_histories[user_id].clear()
    await message.answer(
        "🔄 Історію розмови очищено. Починаємо спочатку!",
        reply_markup=QUICK_REPLIES,
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Довідка."""
    await message.answer(
        "ℹ️ *Як користуватись ботом:*\n\n"
        "1. Вкажіть номер замовлення: `Де моє замовлення 777?`\n"
        "2. Додайте email: `ivan@example.com`\n"
        "3. Або просто запитайте будь-що про магазин\n\n"
        "*Команди:*\n"
        "/start — перезапустити бота\n"
        "/clear — очистити історію розмови\n"
        "/help — ця довідка",
        parse_mode="Markdown",
        reply_markup=QUICK_REPLIES,
    )


@router.message(F.text == "🔄 Очистити історію")
async def clear_history_button(message: Message):
    """Кнопка очищення через клавіатуру."""
    await cmd_clear(message)


@router.message(F.text)
async def handle_message(message: Message):
    """
    Головний обробник текстових повідомлень.
    Передає запит до агента з typing-індикатором.
    """
    user_id = message.from_user.id
    user_text = message.text.strip()

    # Маппінг quick reply кнопок
    button_mapping = {
        "📦 Статус замовлення": "Як я можу перевірити статус мого замовлення?",
        "🕐 Графік роботи": "Який у вас графік роботи?",
        "📞 Контакти підтримки": "Як з вами зв'язатися? Вкажіть контакти підтримки.",
    }
    if user_text in button_mapping:
        user_text = button_mapping[user_text]

    logger.info(f"[Handler] Message from user_id={user_id}: {user_text[:100]}")

    # Показуємо "друкує..." поки агент думає
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # Запускаємо агент в executor щоб не блокувати event loop
    try:
        history = conversation_histories[user_id]

        # Тримаємо не більше 20 повідомлень в контексті (10 turns)
        if len(history) > 20:
            history = history[-20:]
            conversation_histories[user_id] = history

        # Typing-пінгер — продовжуємо показувати "друкує..." кожні 4с
        typing_task = asyncio.create_task(
            _keep_typing(message, interval=4)
        )

        try:
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None,
                lambda: run_agent(user_text, history),
            )
        finally:
            typing_task.cancel()

        try:
            await message.answer(
                response_text,
                parse_mode="Markdown",
                reply_markup=QUICK_REPLIES,
            )
        except Exception as md_err:
            # Якщо Markdown не вдалось спарсити — надсилаємо без форматування
            logger.warning(f"[Handler] Markdown parse failed, sending plain text: {md_err}")
            await message.answer(
                response_text,
                reply_markup=QUICK_REPLIES,
            )

    except Exception as e:
        logger.exception(f"[Handler] Error processing message: {e}")
        await message.answer(
            "⚠️ Вибачте, сталася технічна помилка. "
            "Будь ласка, спробуйте пізніше або зверніться на гарячу лінію: *0 800 500 123*",
            parse_mode="Markdown",
            reply_markup=QUICK_REPLIES,
        )


async def _keep_typing(message: Message, interval: int = 4):
    """Надсилає typing action кожні interval секунд."""
    try:
        while True:
            await asyncio.sleep(interval)
            await message.bot.send_chat_action(
                chat_id=message.chat.id, action="typing"
            )
    except asyncio.CancelledError:
        pass
