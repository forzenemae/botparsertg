import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 300))
YOUR_TELEGRAM_ID = int(os.getenv("YOUR_TELEGRAM_ID", 0))

# Прокси для Telegram (если не работает через обычный)
PROXY = os.getenv("PROXY", "socks5://45.94.46.35:1080")  # Можно заменить