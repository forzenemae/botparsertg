from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from shops import SHOPS

def get_shop_keyboard() -> InlineKeyboardMarkup:
    keyboard = []
    for shop_id, shop_data in SHOPS.items():
        button = InlineKeyboardButton(
            text=f"🏪 {shop_data['name']}",
            callback_data=f"shop_{shop_id}"
        )
        keyboard.append([button])
    
    keyboard.append([
        InlineKeyboardButton(text="📊 Текущий магазин", callback_data="status")
    ])
    keyboard.append([
        InlineKeyboardButton(text="🔄 Перезапустить поиск", callback_data="restart")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_main_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="📋 Выбрать магазин", callback_data="show_shops")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="status")],
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="restart")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)