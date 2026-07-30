import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from config import BOT_TOKEN, CHECK_INTERVAL, YOUR_TELEGRAM_ID
from parser import fetch_ads_with_check
from shops import get_shop_url, get_shop_name, get_shop_description, get_shop_check_words, SHOPS, CURRENT_SHOP
from datetime import datetime
import traceback
import sys
import os

# ============================================================
# ДОБАВЛЯЕМ ПУТЬ ДЛЯ РАБОТЫ НА СЕРВЕРЕ
# ============================================================
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# НАСТРОЙКА БОТА
# ============================================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ============================================================
# ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
# ============================================================
sent_urls = set()
is_searching = True
current_shop = CURRENT_SHOP
shop_name = get_shop_name(CURRENT_SHOP)

# Храним chat_id для каждого пользователя
user_chat_ids = set()

# Добавляем владельца при запуске
if YOUR_TELEGRAM_ID:
    user_chat_ids.add(YOUR_TELEGRAM_ID)

# ============================================================
# КЛАВИАТУРЫ (МЕНЮ)
# ============================================================
def get_main_keyboard():
    """Главное меню"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏪 Выбрать магазин", callback_data="shops")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
            [
                InlineKeyboardButton(text="🔄 Начать поиск", callback_data="start_search"),
                InlineKeyboardButton(text="⏹ Остановить", callback_data="stop_search")
            ],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
        ]
    )
    return keyboard

def get_shops_keyboard():
    """Клавиатура со списком магазинов"""
    keyboard = []
    for shop_id in SHOPS:
        shop_name_item = SHOPS[shop_id]["name"]
        if shop_id == current_shop:
            shop_name_item = f"✅ {shop_name_item}"
        keyboard.append([InlineKeyboardButton(text=shop_name_item, callback_data=f"shop_{shop_id}")])
    
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ============================================================
# ОТПРАВКА СООБЩЕНИЙ
# ============================================================
async def send_message(chat_id: int, text: str):
    if not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    
    for attempt in range(3):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, timeout=30) as resp:
                    result = await resp.json()
                    if result.get("ok"):
                        return True
                    else:
                        print(f"❌ Ошибка API: {result}")
                        return False
        except Exception as e:
            print(f"⚠️ Попытка {attempt+1}: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
            else:
                return False
    return False

# ============================================================
# КОМАНДЫ
# ============================================================
@dp.message(Command("start"))
async def start_command(message: Message):
    global user_chat_ids
    
    user_id = message.from_user.id
    user_chat_ids.add(user_id)
    
    print(f"\n✅ [ЛОГ] /start от {user_id}")
    print(f"   📌 Всего пользователей: {len(user_chat_ids)}")
    
    welcome_text = (
        f"👟 <b>Бот для поиска кроссовок с чеком</b>\n\n"
        f"📍 Текущий магазин: <b>{shop_name}</b>\n"
        f"🔄 Статус: {'🟢 Активен' if is_searching else '🔴 Остановлен'}\n\n"
        f"Выберите действие в меню:"
    )
    
    try:
        await message.answer(
            text=welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode="HTML"
        )
        print(f"   ✅ Приветствие отправлено {user_id}")
    except Exception as e:
        print(f"   ❌ Ошибка отправки приветствия: {e}")

@dp.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "❓ <b>Помощь</b>\n\n"
        "Бот ищет объявления на Avito и присылает те, где есть слово 'чек'.\n\n"
        "<b>Команды:</b>\n"
        "/start — запустить бота\n"
        "/help — эта справка\n\n"
        "<b>Кнопки:</b>\n"
        "🏪 Выбрать магазин — переключиться между магазинами\n"
        "📊 Статистика — сколько объявлений найдено\n"
        "🔄 Начать поиск — возобновить поиск\n"
        "⏹ Остановить — приостановить поиск"
    )
    await message.answer(help_text, parse_mode="HTML")

# ============================================================
# ОБРАБОТКА ВСЕХ СООБЩЕНИЙ (для логов)
# ============================================================
@dp.message()
async def log_all_messages(message: Message):
    print(f"\n📩 [ЛОГ] Сообщение от {message.from_user.username or message.from_user.id}: {message.text or 'не текстовое'}")

# ============================================================
# ОБРАБОТКА КНОПОК
# ============================================================
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    global current_shop, shop_name, is_searching, sent_urls, user_chat_ids
    
    data = callback.data
    user = callback.from_user.id
    
    # Игнорируем неизвестные кнопки (от старых версий)
    if data not in ["shops", "stats", "start_search", "stop_search", "help", "back"] and not data.startswith("shop_"):
        print(f"   ⚠️ Неизвестная кнопка '{data}' от {user}")
        await callback.answer("❌ Устаревшая кнопка, обновите бота", show_alert=False)
        return
    
    user_chat_ids.add(user)
    print(f"\n✅ [ЛОГ] Кнопка '{data}' от {user}")
    
    try:
        if data == "shops":
            await callback.message.edit_text(
                "🏪 <b>Выберите магазин:</b>",
                reply_markup=get_shops_keyboard(),
                parse_mode="HTML"
            )
        elif data.startswith("shop_"):
            shop_id = data.replace("shop_", "")
            current_shop = shop_id
            shop_name = get_shop_name(shop_id)
            sent_urls = set()
            await callback.message.edit_text(
                f"✅ <b>Магазин изменён!</b>\n\n"
                f"🏪 <b>{shop_name}</b>\n"
                f"📝 {get_shop_description(shop_id)}\n\n"
                f"🔄 Поиск начинается заново.",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer(f"Выбран магазин: {shop_name}")
        elif data == "back":
            await callback.message.edit_text(
                f"👟 <b>Бот для поиска кроссовок с чеком</b>\n\n"
                f"📍 Текущий магазин: <b>{shop_name}</b>\n"
                f"🔄 Статус: {'🟢 Активен' if is_searching else '🔴 Остановлен'}\n\n"
                f"Выберите действие:",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        elif data == "stats":
            stats_text = (
                f"📊 <b>Статистика</b>\n\n"
                f"🏪 Магазин: <b>{shop_name}</b>\n"
                f"📨 Отправлено объявлений: <b>{len(sent_urls)}</b>\n"
                f"🔄 Статус: {'🟢 Активен' if is_searching else '🔴 Остановлен'}"
            )
            await callback.message.edit_text(
                stats_text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        elif data == "start_search":
            is_searching = True
            print(f"   ▶️ Поиск ВКЛЮЧЁН (is_searching = {is_searching})")
            await callback.message.edit_text(
                f"🔄 <b>Поиск возобновлён!</b>\n\n"
                f"🏪 Магазин: <b>{shop_name}</b>",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("Поиск запущен")
        elif data == "stop_search":
            is_searching = False
            print(f"   ⏹ Поиск ВЫКЛЮЧЁН (is_searching = {is_searching})")
            await callback.message.edit_text(
                f"⏹ <b>Поиск остановлен!</b>\n\n"
                f"🔄 Чтобы возобновить — нажмите 'Начать поиск'",
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("Поиск остановлен")
        elif data == "help":
            help_text = (
                "❓ <b>Помощь</b>\n\n"
                "Бот ищет объявления на Avito и присылает те, где есть слово 'чек'.\n\n"
                "🏪 <b>Выбрать магазин</b> — переключиться между магазинами\n"
                "📊 <b>Статистика</b> — сколько объявлений найдено\n"
                "🔄 <b>Начать поиск</b> — возобновить поиск\n"
                "⏹ <b>Остановить</b> — приостановить поиск"
            )
            await callback.message.edit_text(
                help_text,
                reply_markup=get_main_keyboard(),
                parse_mode="HTML"
            )
        await callback.answer()
    except Exception as e:
        print(f"⚠️ Ошибка обработки callback: {e}")
        await callback.answer("⚠️ Ошибка", show_alert=False)

# ============================================================
# ФОНОВАЯ ЗАДАЧА
# ============================================================
async def send_ad_immediately(ad_data: dict, shop_name: str):
    global sent_urls, user_chat_ids, is_searching
    
    if not is_searching:
        print(f"   ⏸️ Поиск остановлен, пропускаю: {ad_data.get('title', '')[:30]}")
        return
    
    url = ad_data.get('url')
    if not url or url in sent_urls:
        return
    
    message = (
        f"✅ НОВОЕ ОБЪЯВЛЕНИЕ С ЧЕКОМ!\n"
        f"🏪 {shop_name}\n"
        f"📌 {ad_data.get('title', 'Без названия')}\n"
        f"💰 {ad_data.get('price', 'Цена не указана')}\n"
        f"📝 {ad_data.get('description', 'Описание отсутствует')}\n"
        f"🔗 {url}"
    )
    
    print(f"   📌 Отправляю {len(user_chat_ids)} пользователям")
    
    success_count = 0
    for user_id in list(user_chat_ids):
        if await send_message(user_id, message):
            success_count += 1
            print(f"   ✅ Отправлено {user_id}")
        else:
            print(f"   ❌ Не отправлено {user_id}")
    
    if success_count > 0:
        sent_urls.add(url)
        print(f"✅ Отправлено {success_count} пользователям!")

async def check_new_ads():
    global current_shop, is_searching
    
    while True:
        try:
            if not is_searching:
                await asyncio.sleep(2)
                continue
                
            shop_url = get_shop_url(current_shop)
            shop_name_local = get_shop_name(current_shop)
            check_words = get_shop_check_words(current_shop)
            
            if not shop_url:
                await asyncio.sleep(CHECK_INTERVAL)
                continue
            
            print(f"\n🔍 Проверяю: {shop_name_local} в {datetime.now().strftime('%H:%M:%S')}")
            
            def on_ad_found(ad_data):
                asyncio.create_task(send_ad_immediately(ad_data, shop_name_local))
            
            await fetch_ads_with_check(shop_url, check_words, on_ad_found)
            await asyncio.sleep(CHECK_INTERVAL)
            
        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
            traceback.print_exc()
            await asyncio.sleep(5)

# ============================================================
# ОСНОВНАЯ ФУНКЦИЯ С АВТОПЕРЕЗАПУСКОМ ПРИ КОНФЛИКТЕ
# ============================================================
async def main():
    print("=" * 50)
    print("👟 БОТ ЗАПУЩЕН С МЕНЮ")
    print("=" * 50)
    print(f"🏪 Магазин: {shop_name}")
    print(f"⏱ Интервал: {CHECK_INTERVAL} сек.")
    print(f"📌 Пользователей в списке: {len(user_chat_ids)}")
    print("=" * 50)
    print("ℹ️  Бот работает. Для остановки нажмите Ctrl+C")
    print("=" * 50 + "\n")
    
    # Запускаем фоновую задачу
    asyncio.create_task(check_new_ads())
    
    # Запускаем бота с автоперезапуском при конфликте
    while True:
        try:
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            if "Conflict" in str(e):
                print("🔄 Обнаружен конфликт ботов. Перезапуск через 5 секунд...")
                await asyncio.sleep(5)
            else:
                print("🔄 Перезапуск через 5 секунд...")
                await asyncio.sleep(5)

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")
        print(f"📊 Всего найдено объявлений: {len(sent_urls)}")
    start_bot()
