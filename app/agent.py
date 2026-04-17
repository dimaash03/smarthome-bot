"""
Агентський цикл (Agentic Loop) — чиста реалізація через Anthropic SDK.
Без LangChain, LlamaIndex чи інших фреймворків для агентів.
"""
import logging
import re
from typing import Optional

import anthropic

from app.config import settings
from app.tools.definitions import TOOLS
from app.tools.executor import execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ти — Макс, ввічливий та уважний асистент служби підтримки інтернет-магазину розумної техніки «SmartHome Pro».

📋 Основні правила:
- Завжди відповідай українською мовою
- Будь привітним, терплячим та корисним
- Звертайся до клієнта по імені, якщо воно відоме
- Якщо клієнт є VIP або Gold — окремо подякуй за лояльність

🏪 Інформація про магазин:
- Графік роботи: щодня з 09:00 до 20:00 (Київський час)
- Телефон гарячої лінії: 0 800 500 123 (безкоштовно)
- Email підтримки: support@smarthome.pro
- Сайт: smarthome.pro

📦 Статуси замовлень:
- "processing" → "В обробці"
- "shipped" → "Відправлено"
- "in_transit" → "В дорозі"
- "delivered" → "Доставлено"
- "cancelled" → "Скасовано"

⚠️ Важливо:
- Якщо клієнт надав email — спочатку дізнайся його дані через get_client_info
- Якщо клієнт надав номер замовлення — перевір статус через get_order_status
- Якщо замовлення не знайдено — ввічливо повідом та запропонуй перевірити номер або звернутись на гарячу лінію
- Перед кожним викликом інструменту зафіксуй свої міркування у тегах <thinking>...</thinking>
- Теги <thinking> — лише для логів, не відображай їх у відповіді клієнту
"""

MAX_ITERATIONS = 10  # захист від нескінченного циклу


def run_agent(user_message: str, conversation_history: Optional[list] = None) -> str:
    """
    Запускає агентський цикл для обробки повідомлення користувача.
    
    Args:
        user_message: Повідомлення від користувача
        conversation_history: Попередня історія розмови (для multi-turn)
    
    Returns:
        Фінальна текстова відповідь агента
    """
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Ініціалізуємо або копіюємо історію
    messages = list(conversation_history) if conversation_history else []
    messages.append({"role": "user", "content": user_message})

    logger.info(f"[Agent] Starting agentic loop. User: {user_message[:100]}...")

    for iteration in range(MAX_ITERATIONS):
        logger.info(f"[Agent] Iteration {iteration + 1}/{MAX_ITERATIONS}")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        logger.info(f"[Agent] stop_reason={response.stop_reason}, blocks={len(response.content)}")

        # --- Обробка thinking тегів у тексті ---
        for block in response.content:
            if block.type == "text" and "<thinking>" in block.text:
                thinking_matches = re.findall(r"<thinking>(.*?)</thinking>", block.text, re.DOTALL)
                for thought in thinking_matches:
                    logger.info(f"[Agent] 🤔 Thinking: {thought.strip()}")

        # --- Фінальна відповідь (end_turn без tool_use) ---
        if response.stop_reason == "end_turn":
            final_text = _extract_text(response.content)
            # Прибираємо теги <thinking> з відповіді для клієнта
            final_text = re.sub(r"<thinking>.*?</thinking>", "", final_text, flags=re.DOTALL).strip()
            logger.info(f"[Agent] Final answer: {final_text[:150]}...")

            # Оновлюємо conversation_history якщо передано
            if conversation_history is not None:
                conversation_history.append({"role": "user", "content": user_message})
                conversation_history.append({"role": "assistant", "content": response.content})

            return final_text

        # --- Обробка виклику інструментів ---
        if response.stop_reason == "tool_use":
            # Додаємо відповідь асистента (з tool_use блоками) до messages
            messages.append({"role": "assistant", "content": response.content})

            # Збираємо результати всіх tool_use блоків
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"[Agent] 🔧 Tool call: {block.name}({block.input})")
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            # Повертаємо результати інструментів
            messages.append({"role": "user", "content": tool_results})
            continue

        # --- Неочікувана зупинка ---
        logger.warning(f"[Agent] Unexpected stop_reason: {response.stop_reason}")
        break

    logger.error("[Agent] Max iterations reached without final answer")
    return "Вибачте, сталася помилка при обробці вашого запиту. Будь ласка, спробуйте ще раз або зверніться на гарячу лінію: 0 800 500 123."


def _extract_text(content_blocks: list) -> str:
    """Витягує текст з контентних блоків відповіді Claude."""
    texts = []
    for block in content_blocks:
        if block.type == "text" and block.text.strip():
            texts.append(block.text.strip())
    return "\n".join(texts)
