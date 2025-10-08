from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def user_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Übung starten")],
            [KeyboardButton(text="📊 Statistik"), KeyboardButton(text="⚙️ Einstellungen")]
        ],
        resize_keyboard=True
    )