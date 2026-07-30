from flask import Flask, request
import threading
import asyncio
import os
import sys
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Импортируем бота
try:
    from bot import bot, dp, main as bot_main
    from config import BOT_TOKEN
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    BOT_TOKEN = None

# Запускаем бота в отдельном потоке
def run_bot():
    try:
        if BOT_TOKEN:
            print("🤖 Запускаю бота...")
            asyncio.run(bot_main())
        else:
            print("❌ Нет токена!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

# Запускаем бота при старте
thread = threading.Thread(target=run_bot)
thread.daemon = True
thread.start()

@app.route('/')
def index():
    return "👟 Бот работает! Версия 1.0"

@app.route('/ping')
def ping():
    return "Pong!", 200

@app.route('/health')
def health():
    if BOT_TOKEN:
        return "OK", 200
    return "No token", 500

@app.route('/status')
def status():
    return {
        "status": "running",
        "bot_token": "present" if BOT_TOKEN else "missing",
        "thread": "alive" if thread.is_alive() else "dead"
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)