# 🏠 SmartHome Pro — Telegram Support Bot

Telegram-бот підтримки для інтернет-магазину «SmartHome Pro» на базі **Claude (Anthropic API)** з реальною інтеграцією **Google Sheets** через **Tool Use (Function Calling)**.

## 🏗 Архітектура

```
Користувач (Telegram)
       │
       ▼
  aiogram 3.x  ──────────────── handlers.py
       │
       ▼
  Agentic Loop ──────────────── agent.py
       │
       ├── [tool_use] ──────── tools/executor.py
       │                             │
       │                    sheets/client.py
       │                             │
       │                      Google Sheets API
       │                    (Clients + Orders)
       │
       └── [end_turn] ──── відповідь → Telegram
```

### Ключові файли

| Файл | Призначення |
|------|-------------|
| `main.py` | Точка входу, запуск бота |
| `app/agent.py` | **Agentic Loop** — чиста реалізація без фреймворків |
| `app/handlers.py` | Telegram-хендлери (aiogram 3.x) |
| `app/tools/definitions.py` | JSON Schema для інструментів Claude |
| `app/tools/executor.py` | Диспетчер виклику інструментів |
| `app/sheets/client.py` | Інтеграція з Google Sheets (gspread) |
| `app/config.py` | Конфігурація через pydantic-settings |

---

## ⚙️ Як запустити

### 1. Клонування репозиторію

```bash
git clone https://github.com/YOUR_USERNAME/smarthome-bot.git
cd smarthome-bot
```

### 2. Встановлення залежностей

```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
# або: venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

### 3. Налаштування змінних середовища

```bash
cp .env.example .env
```

Відредагуй `.env`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ANTHROPIC_API_KEY=your_anthropic_api_key
GOOGLE_SHEETS_ID=your_google_sheets_id
GOOGLE_SERVICE_ACCOUNT_FILE=service_account.json
```

### 4. Налаштування Google Sheets

#### 4.1 Скопіюй таблицю

Відкрий [SmartHome Pro Database](https://docs.google.com/spreadsheets/d/...) → **Файл → Зробити копію** на свій Google Диск.

Скопіюй **ID таблиці** з URL (між `/d/` та `/edit`):
```
https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit
                                        ↑ це і є GOOGLE_SHEETS_ID
```

#### 4.2 Створи сервісний акаунт Google Cloud

1. Відкрий [Google Cloud Console](https://console.cloud.google.com/)
2. Створи новий проєкт або вибери існуючий
3. **APIs & Services → Enable APIs** → увімкни:
   - **Google Sheets API**
   - **Google Drive API**
4. **IAM & Admin → Service Accounts → Create Service Account**
   - Назва: `smarthome-bot`
   - Role: `Viewer` (або `Editor` якщо потрібен запис)
5. **Keys → Add Key → Create new key → JSON**
   - Збережи файл як `service_account.json` у корені проєкту

#### 4.3 Надай доступ сервісному акаунту

Скопіюй email сервісного акаунту (вигляд: `smarthome-bot@project.iam.gserviceaccount.com`)

У Google Sheets → **Поділитись** → вставте email сервісного акаунту → **Viewer**.

### 5. Запуск

```bash
python main.py
```

---

## 🤖 Як працює Agentic Loop

```python
# app/agent.py — спрощена схема

messages = [{"role": "user", "content": user_message}]

while iterations < MAX_ITERATIONS:
    response = claude.messages.create(
        model="claude-3-5-sonnet-20241022",
        tools=TOOLS,          # get_client_info, get_order_status
        messages=messages,
    )

    if response.stop_reason == "end_turn":
        return extract_text(response)   # ✅ Фінальна відповідь

    if response.stop_reason == "tool_use":
        messages.append(assistant_response)
        
        for tool_call in response.content:
            result = execute_tool(tool_call.name, tool_call.input)
            messages.append(tool_result(result))
        
        continue  # 🔄 Наступна ітерація
```

Агент самостійно вирішує:
- Чи потрібен виклик інструменту
- Які інструменти викликати (і в якому порядку)
- Коли дати фінальну відповідь

---

## 🧪 Тестові сценарії

| Сценарій | Очікувана поведінка |
|----------|---------------------|
| `"Привіт! Це Іван (ivan@example.com). Що там з моїм замовленням 777?"` | Виклик `get_client_info` + `get_order_status`, відповідь з іменем |
| `"Який у вас графік роботи?"` | Відповідь з system prompt, без виклику tools |
| `"Де моє замовлення 12345? Пошта ivan@example.com"` | Повідомлення про ненайдене замовлення |

---

## 📱 Команди бота

| Команда | Дія |
|---------|-----|
| `/start` | Привітання + швидкі кнопки |
| `/help` | Довідка по використанню |
| `/clear` | Очистити контекст розмови |

---

## 🗄 Структура Google Sheets

### Лист `Clients`
| email | name | loyalty_status |
|-------|------|----------------|
| ivan@example.com | Іван Петренко | Gold |

### Лист `Orders`
| order_id | client_email | status | delivery_date |
|----------|-------------|--------|---------------|
| 777 | ivan@example.com | shipped | 2025-02-01 |

---

## 📦 Стек технологій

- **Python 3.11+**
- **aiogram 3.x** — Telegram Bot Framework
- **anthropic** — офіційний SDK для Claude API
- **gspread + google-auth** — Google Sheets інтеграція
- **pydantic-settings** — конфігурація через .env

> ⛔ LangChain, LlamaIndex, AutoGen та інші агентські фреймворки **не використовуються**.
> Agentic Loop реалізовано вручну через чистий Anthropic SDK.
