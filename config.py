import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DB_PATH = os.getenv("DB_PATH", "data/bot.db")
DEFAULT_DELAY_MS = int(os.getenv("DEFAULT_DELAY_MS", "1200"))
DEFAULT_CYCLE_SECONDS = int(os.getenv("DEFAULT_CYCLE_SECONDS", "3600"))
