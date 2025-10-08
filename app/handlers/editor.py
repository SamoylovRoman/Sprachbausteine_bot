from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommandScopeChat, \
    ReplyKeyboardRemove
from sqlalchemy.orm import joinedload

from app.db.enums import UserRole
from app.keyboards import editor as kb
from app.db.models import Category, Level, User, Example, Answer, AccessCode, example_levels
from aiogram.filters import Command, CommandStart
from app.db.session import SessionLocal
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.bot_commands import editor_commands, user_commands
from aiogram.client.bot import Bot

router = Router()

class AccessCodeFSM(StatesGroup):
    waiting_for_code = State()

# === FSM for adding access codes ===
class AccessCodeAddFSM(StatesGroup):
    waiting_for_codes = State()

# === FSM States for adding example ===
class ExampleAddFSM(StatesGroup):
    waiting_for_sentence = State()
    waiting_for_correct_answer = State()
    waiting_for_explanation = State()
    waiting_for_incorrect_answers = State()
    waiting_for_category = State()
    waiting_for_levels = State()
    preview_and_confirm = State()

# === FSM States for listing examples ===
class ExampleListFSM(StatesGroup):
    browsing = State()
    viewing = State()

# === Pagination Settings ===
EXAMPLES_PER_PAGE = 10

def is_user(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user and user.role == UserRole.USER.value

def is_editor(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user and user.role == UserRole.EDITOR.value

def is_admin(user_id: int) -> bool:
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    return user and user.role == UserRole.ADMIN.value


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    # Clear any previous FSM state (in case user comes from old version)
    await state.clear()

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()

        if not user:
            # Create a new user without any access code
            user = User(
                id=message.from_user.id,
                username=(message.from_user.username or message.from_user.full_name),
                role=UserRole.USER.value
            )
            session.add(user)
            session.commit()

        # Reset bot commands before setting actual ones
        await message.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=message.chat.id))
    finally:
        session.close()

    await _show_main_menu(message, state)


async def _show_main_menu(message: Message, state: FSMContext):
    bot: Bot = message.bot

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(id=message.from_user.id).first()
        if not user:
            await message.answer("⚠️ Benutzer nicht gefunden.")
            return

        if user.role == UserRole.EDITOR.value:
            # Configure editor-specific commands
            await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=message.chat.id))
            await bot.set_my_commands(editor_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
            await message.answer(
                "👋 Willkommen, Redakteur! Hier sind deine verfügbaren Befehle.",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer("Wähle eine Option aus dem Menü unten 👇")
        else:
            # Configure normal user commands
            await bot.set_my_commands(user_commands, scope=BotCommandScopeChat(chat_id=message.chat.id))
            await message.answer(
                "Hallo! 👋 Ich helfe dir beim Training für die Sprachbausteine.",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer("Wähle aus dem Menü unten, was du machen möchtest 👇")
    finally:
        session.close()


@router.message(Command("add_example"))
async def start_example_addition(message: Message, state: FSMContext):
    if not is_editor(message.from_user.id):
        await message.delete()
        return
    await state.set_state(ExampleAddFSM.waiting_for_sentence)
    await message.answer("✏️ Gib ein Beispielsatz ein. Markiere die Lücke mit [x].")


@router.message(ExampleAddFSM.waiting_for_sentence)
async def handle_sentence(message: Message, state: FSMContext):
    if "[x]" not in message.text:
        await message.answer("⚠️ Bitte markiere die Lücke mit [x]. Versuche es erneut.")
        return
    await state.update_data(sentence=message.text)
    await state.set_state(ExampleAddFSM.waiting_for_correct_answer)
    await message.answer("✅ Was ist die richtige Antwort?")


@router.message(ExampleAddFSM.waiting_for_correct_answer)
async def handle_correct_answer(message: Message, state: FSMContext):
    await state.update_data(correct_answer=message.text)
    await state.set_state(ExampleAddFSM.waiting_for_explanation)
    await message.answer("🧾 Gib eine kurze Erklärung oder Begründung an:")


@router.message(ExampleAddFSM.waiting_for_explanation)
async def handle_explanation(message: Message, state: FSMContext):
    await state.update_data(explanation=message.text)
    await state.set_state(ExampleAddFSM.waiting_for_incorrect_answers)
    await message.answer("❌ Gib falsche Antworten durch Kommas getrennt ein:")


@router.message(ExampleAddFSM.waiting_for_incorrect_answers)
async def handle_incorrect_answers(message: Message, state: FSMContext):
    incorrect = [s.strip() for s in message.text.split(",") if s.strip()]
    if len(incorrect) < 2:
        await message.answer("Bitte gib mindestens zwei falsche Antworten ein.")
        return
    await state.update_data(incorrect_answers=incorrect)

    # Категории из БД
    session = SessionLocal()
    categories = session.query(Category).all()
    session.close()

    buttons = [[InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")] for cat in categories]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await state.set_state(ExampleAddFSM.waiting_for_category)
    await message.answer("📚 Wähle eine Kategorie:", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("cat_"))
async def handle_category_selection(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[1])
    await state.update_data(category_id=cat_id, selected_levels=[])
    await state.set_state(ExampleAddFSM.waiting_for_levels)
    await show_level_selection(callback, state)


async def show_level_selection(callback: CallbackQuery, state: FSMContext):
    session = SessionLocal()
    levels = session.query(Level).all()
    session.close()

    data = await state.get_data()
    selected_levels = data.get("selected_levels", [])

    buttons = []
    for level in levels:
        label = f"✔️ {level.name}" if level.id in selected_levels else level.name
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"level_toggle_{level.id}")])

    buttons.append([InlineKeyboardButton(text="✅ Fertig", callback_data="level_done")])

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text("Bitte wähle bis zu zwei aufeinanderfolgende Niveaus:", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("level_toggle_"))
async def handle_level_toggle(callback: CallbackQuery, state: FSMContext):
    level_id = int(callback.data.split("_")[-1])
    data = await state.get_data()
    selected = data.get("selected_levels", [])

    if level_id in selected:
        selected.remove(level_id)
    else:
        selected.append(level_id)

    await state.update_data(selected_levels=selected)
    await show_level_selection(callback, state)


@router.callback_query(lambda c: c.data == "level_done")
async def handle_level_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected_levels", [])

    if not selected:
        await callback.answer("❗️Bitte wähle mindestens ein Sprachniveau aus.", show_alert=True)
        return

    if len(selected) > 2:
        await callback.answer("❗️Maximal zwei Niveaus erlaubt.", show_alert=True)
        return

    if len(selected) == 2 and abs(selected[0] - selected[1]) != 1:
        await callback.answer("❗️Die gewählten Niveaus müssen aufeinanderfolgend sein.", show_alert=True)
        return

    await state.set_state(ExampleAddFSM.preview_and_confirm)
    await callback.message.edit_reply_markup()

    # Предпросмотр
    session = SessionLocal()
    levels = session.query(Level).filter(Level.id.in_(selected)).all()
    category = session.query(Category).filter(Category.id == data["category_id"]).first()
    session.close()

    preview = (
        f"📋 Vorschau des Beispiels:\n\n"
        f"📝 Satz: {data['sentence']}\n"
        f"✅ Richtig: {data['correct_answer']}\n"
        f"❌ Falsch: {', '.join(data['incorrect_answers'])}\n"
        f"💬 Erklärung: {data['explanation']}\n"
        f"🏷️ Kategorie: {category.name}\n"
        f"🧠 Niveau: {', '.join(lv.name for lv in levels)}"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💾 Speichern", callback_data="save_example")],
        [InlineKeyboardButton(text="❌ Abbrechen", callback_data="cancel_example")],
    ])
    await callback.message.answer(preview, reply_markup=buttons)


@router.callback_query(lambda c: c.data == "cancel_example")
async def handle_cancel_example(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup()
    await callback.message.answer("❌ Beispiel wurde nicht gespeichert.")


@router.callback_query(lambda c: c.data == "save_example")
async def handle_save_example(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = SessionLocal()

    example = Example(
        sentence=data['sentence'],
        explanation=data['explanation'],
        category_id=data['category_id'],
        created_by=callback.from_user.id
    )
    session.add(example)
    session.flush()

    for level_id in data['selected_levels']:
        level = session.query(Level).filter_by(id=level_id).first()
        example.levels.append(level)

    session.add_all([
        Answer(example_id=example.id, text=data['correct_answer'], is_correct=True),
        *[
            Answer(example_id=example.id, text=ans, is_correct=False)
            for ans in data['incorrect_answers']
        ]
    ])

    session.commit()
    session.close()

    await state.clear()
    await callback.message.edit_reply_markup()
    await callback.message.answer("✅ Beispiel wurde erfolgreich gespeichert.")


def get_example_list_markup(page: int, examples: list[Example], total: int):
    buttons = [[
        InlineKeyboardButton(text=e.sentence[:50] + ("..." if len(e.sentence) > 50 else ""), callback_data=f"view_example_{e.id}")
    ] for e in examples]

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Zurück", callback_data=f"page_{page - 1}"))
    if page * EXAMPLES_PER_PAGE < total:
        nav_buttons.append(InlineKeyboardButton(text="➡️ Weiter", callback_data=f"page_{page + 1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("list_examples"))
async def list_examples(message: Message, state: FSMContext):
    if not is_editor(message.from_user.id):
        await message.delete()
        return
    await state.set_state(ExampleListFSM.browsing)
    await show_example_page(message, state, 1)


@router.callback_query(lambda c: c.data.startswith("page_"))
async def paginate_examples(callback: CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await show_example_page(callback.message, state, page, edit=True)
    await callback.answer()


async def show_example_page(target: Message, state: FSMContext, page: int, edit=False):
    session = SessionLocal()
    total = session.query(Example).count()
    examples = (
        session.query(Example)
        .order_by(Example.sentence)  # 🔠 Алфавитная сортировка
        .offset((page - 1) * EXAMPLES_PER_PAGE)
        .limit(EXAMPLES_PER_PAGE)
        .all()
    )
    session.close()

    markup = get_example_list_markup(page, examples, total)
    if edit:
        await target.edit_text("📋 Liste der Beispiele:", reply_markup=markup)
    else:
        await target.answer("📋 Liste der Beispiele:", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("view_example_"))
async def view_example_detail(callback: CallbackQuery, state: FSMContext):
    example_id = int(callback.data.split("_")[2])
    session = SessionLocal()

    example = session.query(Example).options(
        joinedload(Example.answers),
        joinedload(Example.category),
        joinedload(Example.levels)
    ).filter(Example.id == example_id).first()

    session.close()

    correct = next((a.text for a in example.answers if a.is_correct), "-")
    incorrect = [a.text for a in example.answers if not a.is_correct]
    incorrect_text = ", ".join(incorrect) if incorrect else "-"
    levels = ", ".join([l.name for l in example.levels]) or "-"
    category = example.category.name if example.category else "-"

    preview_text = (
        "📋 Vorschau des Beispiels:\n\n"
        f"📝 Satz: {example.sentence}\n"
        f"✅ Richtig: {correct}\n"
        f"❌ Falsch: {incorrect_text}\n"
        f"💬 Erkl\u00e4rung: {example.explanation or '-'}\n"
        f"🏷️ Kategorie: {category}\n"
        f"🧠 Niveau: {levels}"
    )

    markup = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Zur\u00fcck", callback_data="back_to_list")]]
    )
    await state.set_state(ExampleListFSM.viewing)
    await callback.message.edit_text(preview_text, reply_markup=markup)
    await callback.answer()


@router.callback_query(lambda c: c.data == "back_to_list")
async def back_to_list(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ExampleListFSM.browsing)
    await show_example_page(callback.message, state, 1, edit=True)
    await callback.answer()


@router.message(Command("add_access_codes"))
async def start_add_codes(message: Message, state: FSMContext):
    if not is_editor(message.from_user.id):
        await message.delete()
        return
    await state.set_state(AccessCodeAddFSM.waiting_for_codes)
    await message.answer("🔐 Bitte gib die Zugangscodes durch Komma getrennt ein:")

@router.message(AccessCodeAddFSM.waiting_for_codes)
async def handle_add_codes(message: Message, state: FSMContext):
    codes_text = message.text
    codes = [c.strip() for c in codes_text.split(",") if c.strip()]

    session = SessionLocal()
    added_count = 0
    for code in codes:
        if not session.query(AccessCode).filter_by(code=code).first():
            new_code = AccessCode(code=code, is_used=False, created_at=datetime.utcnow())
            session.add(new_code)
            added_count += 1

    session.commit()
    session.close()
    await message.answer(f"✅ {added_count} Zugangscode(s) wurden erfolgreich hinzugefügt.")
    await state.clear()

@router.message(F.text, ~F.text.startswith("/"))
async def handle_unexpected_message(message: Message, state: FSMContext):
    current_state = await state.get_state()
    all_commands = {f"/{cmd.command}" for cmd in (editor_commands + user_commands)}
    print(f"FSM: {current_state}\n Command: {all_commands}")

    # Если сообщение — не команда из списка и нет активного состояния
    if (current_state is None and message.text not in all_commands) or (
            current_state is not None and message.text not in all_commands):
        try:
            print(f"Don't do anything")
            await message.delete()
        except:
            pass  # если вдруг нельзя удалить (например, нет прав)

