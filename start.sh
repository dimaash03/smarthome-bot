#!/bin/bash

# SmartHome Pro Bot — скрипт запуску
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Запуск SmartHome Pro Bot..."
echo "📁 Папка: $SCRIPT_DIR"

# Unset any empty system env vars that would override .env
unset ANTHROPIC_API_KEY
unset TELEGRAM_BOT_TOKEN
unset GOOGLE_SHEETS_ID

.venv/bin/python main.py
