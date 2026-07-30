from flask import Flask
import threading
import asyncio
import os
import sys

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)

# Импортируем бота
try:
    from bot import start_bot
    print("✅ Импорт bot успешен")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")

# Простой эндпоинт для проверки
@app.route('/')
def index():
    return "👟 Бот работает! Версия 3.0"

@app.route('/ping')
def ping():
    return "Pong!", 200

@app.route('/health')
def health():
    return "OK", 200

# Функция для запуска бота
def run_bot():
    try:
        start_bot()
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")

if __name__ == '__main__':
    # Запускаем бота в ОТДЕЛЬНОМ потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
