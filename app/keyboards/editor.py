from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def editor_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Ausdruck hinzufügen")],
            [KeyboardButton(text="📋 Ausdruckliste")]
        ],
        resize_keyboard=True
    )

def category_keyboard(selected: list[str] = None):
    if selected is None:
        selected = []

    all_categories = [
        "Präpositionen", "Verben mit Präposition",
        "Konjunktionaladverbien", "Redewendungen",
        "Grammatik", "Wortschatz", "Sonstiges"
    ]

    keyboard = []
    for cat in all_categories:
        prefix = "✅ " if cat in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{cat}",
                callback_data=f"toggle_cat:{cat}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="✅ Fertig", callback_data="confirm_categories")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def level_keyboard(selected: list[str] = None):
    if selected is None:
        selected = []

    all_levels = ["A2", "B1", "B2", "C1", "C2"]
    keyboard = []
    for level in all_levels:
        prefix = "✅ " if level in selected else ""
        keyboard.append([
            InlineKeyboardButton(
                text=f"{prefix}{level}",
                callback_data=f"toggle_lvl:{level}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton(text="✅ Fertig", callback_data="confirm_levels")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)