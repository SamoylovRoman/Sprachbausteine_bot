from datetime import datetime
from enum import Enum

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.db.session import SessionLocal
from app.db.models import Example, Answer, Level, example_levels, UserCategoryStat, Category, UserSettings
import random

router = Router()


# === FSM States for training ===
class TrainingFSM(StatesGroup):
    waiting_for_level = State()
    waiting_for_count = State()
    in_progress = State()

# === FSM for settings ===
class SettingsFSM(StatesGroup):
    waiting_for_time_selection = State()


# === Settings: enumeration of number of answer options ===
class AnswerOptionsCount(Enum):
    THREE = 3
    FOUR = 4
    FIVE = 5


@router.message(Command("start_training"))
async def cmd_training(message: Message, state: FSMContext):
    session = SessionLocal()
    user_settings = session.query(UserSettings).filter_by(user_id=message.from_user.id).first()

    if user_settings and user_settings.language_level:
        level_id = user_settings.language_level
        examples_count = user_settings.examples_count

        if examples_count:
            example_ids = session.query(Example.id).join(example_levels).filter(example_levels.c.level_id == level_id).all()
            selected_ids = random.sample([e[0] for e in example_ids], examples_count)
            level = session.query(Level).filter(Level.id == level_id).first()
            session.close()

            await state.update_data(example_ids=selected_ids, current_index=0, correct_count=0, total_count=len(selected_ids))
            await message.answer(f"🎯 Niveau: {level.name}\n📊 Anzahl der Beispiele: {examples_count}\nLos geht's mit dem Training! ⬇️")
            await send_example(message, state)
        else:
            await state.update_data(level_id=level_id)
            session.close()
            await ask_for_count(message, state)
    else:
        session.close()
        await ask_for_level(message, state)

async def ask_for_level(message: Message, state: FSMContext):
    session = SessionLocal()
    level_buttons = []
    current_row = []

    for level in session.query(Level).all():
        count = session.query(Example).join(example_levels).filter(example_levels.c.level_id == level.id).count()
        if count >= 5:
            current_row.append(InlineKeyboardButton(text=level.name, callback_data=f"train_level_{level.id}"))
            if len(current_row) == 2:
                level_buttons.append(current_row)
                current_row = []

    if current_row:
        level_buttons.append(current_row)

    markup = InlineKeyboardMarkup(inline_keyboard=level_buttons)
    session.close()

    await state.set_state(TrainingFSM.waiting_for_level)
    await message.answer("🧠 Für welches Niveau möchtest du trainieren?", reply_markup=markup)

async def ask_for_count(message: Message, state: FSMContext):
    session = SessionLocal()
    level_id = (await state.get_data()).get("level_id")
    examples_count = session.query(Example).join(example_levels).filter(example_levels.c.level_id == level_id).count()
    level = session.query(Level).filter(Level.id == level_id).first()
    session.close()

    row = []
    for n in [5, 10, 20]:
        if examples_count >= n:
            row.append(InlineKeyboardButton(text=str(n), callback_data=f"train_count_{n}"))

    markup = InlineKeyboardMarkup(inline_keyboard=[row])

    await message.answer(f"✅ Niveau gewählt: {level.name}\nWähle, wie viele Beispiele du trainieren möchtest:", reply_markup=markup)
    await state.update_data(level_name=level.name)
    await state.set_state(TrainingFSM.waiting_for_count)

@router.callback_query(lambda c: c.data.startswith("train_level_"))
async def handle_level_selection(callback: CallbackQuery, state: FSMContext):
    level_id = int(callback.data.split("_")[2])
    session = SessionLocal()

    level = session.query(Level).filter(Level.id == level_id).first()
    examples_count = session.query(Example).join(example_levels).filter(example_levels.c.level_id == level_id).count()
    user_settings = session.query(UserSettings).filter_by(user_id=callback.from_user.id).first()
    session.close()

    await state.update_data(level_id=level_id, total_available=examples_count)
    await state.update_data(level_name=level.name)

    if user_settings and user_settings.examples_count:
        await handle_count_selection_auto(callback, state, user_settings.examples_count, level.name)
    else:
        row = []
        for n in [5, 10, 20]:
            if examples_count >= n:
                row.append(InlineKeyboardButton(text=str(n), callback_data=f"train_count_{n}"))

        markup = InlineKeyboardMarkup(inline_keyboard=[row])

        await callback.message.delete()
        await callback.message.answer(
            f"✅ Niveau gewählt: {level.name}\nWähle, wie viele Beispiele du trainieren möchtest:",
            reply_markup=markup
        )
        await state.set_state(TrainingFSM.waiting_for_count)

async def handle_count_selection_auto(callback: CallbackQuery, state: FSMContext, examples_count: int, level_name: str):
    data = await state.get_data()
    level_id = data.get("level_id")

    session = SessionLocal()
    example_ids = session.query(Example.id).join(example_levels).filter(example_levels.c.level_id == level_id).all()
    selected_ids = random.sample([e[0] for e in example_ids], examples_count)
    session.close()

    await state.update_data(example_ids=selected_ids, current_index=0, correct_count=0, total_count=len(selected_ids))
    await callback.message.delete()
    await callback.message.answer(f"🎯 Niveau: {level_name}\n📊 Anzahl der Beispiele: {examples_count}\nLos geht's mit dem Training! ⬇️")
    await send_example(callback, state)

@router.callback_query(lambda c: c.data.startswith("train_count_"))
async def handle_count_selection(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.split("_")[2])
    data = await state.get_data()
    level_id = data.get("level_id")
    level_name = data.get("level_name")

    session = SessionLocal()
    example_ids = session.query(Example.id).join(example_levels).filter(example_levels.c.level_id == level_id).all()
    selected_ids = random.sample([e[0] for e in example_ids], count)
    session.close()

    await state.update_data(example_ids=selected_ids, current_index=0, correct_count=0, total_count=len(selected_ids))
    await callback.message.delete()
    await callback.message.answer(
        f"🎯 Niveau: {level_name}\n📊 Anzahl der Beispiele: {count}\nLos geht's mit dem Training! ⬇️")
    await send_example(callback, state)

async def send_example(event, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    example_ids = data.get("example_ids", [])

    if current_index >= len(example_ids):
        correct_count = data.get("correct_count", 0)
        total_count = data.get("total_count", 0)
        percent = round(correct_count / total_count * 100) if total_count else 0
        sender = event.message if isinstance(event, CallbackQuery) else event
        await sender.answer(
            f"🏁 Training abgeschlossen!\n"
            f"🎯 Deine Leistung: <b>{percent}%</b> ({correct_count}/{total_count})\n"
            f"🔁 Starte neues Training mit /start_training",
            parse_mode="HTML"
        )
        await state.clear()
        return

    example_id = example_ids[current_index]
    session = SessionLocal()
    example = session.query(Example).filter_by(id=example_id).first()
    correct_answer = session.query(Answer).filter_by(example_id=example.id, is_correct=True).first()
    incorrect_answers = session.query(Answer).filter_by(example_id=example.id, is_correct=False).all()

    user_settings = session.query(UserSettings).filter_by(user_id=event.from_user.id).first()
    answer_count = user_settings.answers_count if user_settings and user_settings.answers_count else 3

    sentence = example.sentence
    category_id = example.category_id
    correct_text = correct_answer.text
    incorrect_sample = [
        a.text for a in random.sample(incorrect_answers, min(answer_count - 1, len(incorrect_answers)))
    ]

    stat = session.query(UserCategoryStat).filter_by(user_id=event.from_user.id, category_id=category_id).first()
    if not stat:
        stat = UserCategoryStat(user_id=event.from_user.id, category_id=category_id, correct_attempts=0, total_attempts=0)
        session.add(stat)
    stat.total_attempts += 1
    session.commit()
    session.close()

    options = [correct_text] + incorrect_sample
    random.shuffle(options)

    buttons = [[InlineKeyboardButton(text=opt, callback_data=f"train_answer_{opt}")] for opt in options]
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    filled_sentence = sentence.replace("[x]", "____")
    await state.update_data(correct_answer=correct_text, current_example_id=example_id)
    sender = event.message if isinstance(event, CallbackQuery) else event
    await sender.answer(f"{current_index + 1}/{len(example_ids)}. 📝 {filled_sentence}", reply_markup=markup)



@router.callback_query(lambda c: c.data.startswith("train_answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    selected = callback.data.replace("train_answer_", "")
    data = await state.get_data()

    correct = data.get("correct_answer")
    current_index = data.get("current_index")
    example_id = data.get("current_example_id")
    # print(f"handle_answer selected = {selected}, correct = {correct}")

    session = SessionLocal()
    example = session.query(Example).filter_by(id=example_id).first()
    category_id = example.category_id

    if selected == correct:
        response = f"✅ <b>Richtig!</b> {selected}"
        stat = session.query(UserCategoryStat).filter_by(user_id=callback.from_user.id, category_id=category_id).first()
        # print(f"handle_answer: stat = {stat}")
        # print(f"handle_answer: user_id  ={callback.from_user.id}, category_id = {category_id}")
        correct_count = data.get("correct_count", 0) + 1
        await state.update_data(correct_count=correct_count)
        if stat:
            stat.correct_attempts += 1
            session.commit()
    else:
        response = f"❌ Falsch. Richtige Antwort: <b>{correct}</b>"

    explanation = example.explanation or "-"
    session.close()

    await callback.message.edit_reply_markup()
    await callback.message.answer(f"{response}\n\n🧾 Erklärung: {explanation}", parse_mode="HTML")
    await state.update_data(current_index=current_index + 1)
    await send_example(callback, state)


# @router.message(Command("my_statistics"))
# async def cmd_statistics(message: Message):
#     session = SessionLocal()
#     stats = session.query(UserCategoryStat).filter_by(user_id=message.from_user.id).all()
#     print(f"cmd_statistics: user_id = {message.from_user.id}")
#
#     if not stats:
#         await message.answer("📊 Du hast noch keine Trainingsstatistiken.")
#         session.close()
#         return
#
#     result_lines = []
#     for stat in stats:
#         category = session.query(Category).filter_by(id=stat.category_id).first()
#         percent = round((stat.correct_attempts / stat.total_attempts) * 100) if stat.total_attempts else 0
#         result_lines.append(
#             f"🏷️ <b>{category.name}</b> — <b>{percent}%</b> ({stat.correct_attempts}/{stat.total_attempts})")
#
#     session.close()
#     final_text = "📊 Deine Statistik nach Kategorien (richtige Antworten):\n\n" + "\n".join(result_lines)
#     await message.answer(final_text, parse_mode="HTML")

@router.message(Command("my_statistics"))
async def cmd_statistics(message: Message):
    # Fetch per-category stats for the user
    session = SessionLocal()
    try:
        stats = session.query(UserCategoryStat).filter_by(user_id=message.from_user.id).all()
        print(f"cmd_statistics: user_id = {message.from_user.id}")

        if not stats:
            await message.answer("📊 Du hast noch keine Trainingsstatistiken.")
            return

        # Prefetch category names in one query to avoid N+1
        category_ids = [s.category_id for s in stats]
        categories = session.query(Category).filter(Category.id.in_(category_ids)).all()
        category_map = {c.id: c.name for c in categories}

        result_lines = []
        total_correct = 0
        total_attempts = 0

        # Build per-category rows and accumulate totals
        for stat in stats:
            name = category_map.get(stat.category_id, f"ID {stat.category_id}")
            percent = round((stat.correct_attempts / stat.total_attempts) * 100) if stat.total_attempts else 0
            result_lines.append(
                f"🏷️ <b>{name}</b> — <b>{percent}%</b> ({stat.correct_attempts}/{stat.total_attempts})"
            )
            total_correct += stat.correct_attempts
            total_attempts += stat.total_attempts

        # Compute overall (global) statistics
        overall_percent = round((total_correct / total_attempts) * 100) if total_attempts else 0
        overall_line = f"\n\n🧮 <b>Gesamt</b> — <b>{overall_percent}%</b> ({total_correct}/{total_attempts})"

        final_text = (
            "📊 Deine Statistik nach Kategorien (richtige Antworten):\n\n"
            + "\n".join(result_lines)
            + overall_line
        )

        await message.answer(final_text, parse_mode="HTML")

    finally:
        # Always close the session
        session.close()


@router.message(Command("bot_settings"))
async def cmd_bot_settings(message: Message):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔢 Antwortanzahl", callback_data="setting_num_choices")],
        # [InlineKeyboardButton(text="⏰ Trainingszeit", callback_data="setting_training_time")],
        # [ InlineKeyboardButton(text="⚙️ Einstellung 3", callback_data="setting_3")]
    ])
    await message.answer("🛠️ Wähle deine Einstellungen:", reply_markup=markup)


@router.callback_query(lambda c: c.data == "setting_training_time")
async def handle_training_time_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SettingsFSM.waiting_for_time_selection)
    time_buttons = []
    times = [
        "06:00", "07:00", "08:00", "09:00",
        "10:00", "11:00", "13:00", "15:00",
        "17:00", "18:30", "20:00", "21:30",
        "22:30", "00:00", "01:00", "02:00"
    ]

    row = []
    for idx, time_str in enumerate(times):
        row.append(InlineKeyboardButton(text=time_str, callback_data=f"train_time_{time_str}"))
        if (idx + 1) % 4 == 0:
            time_buttons.append(row)
            row = []
    if row:
        time_buttons.append(row)

    time_buttons.append([
        InlineKeyboardButton(text="🛑 Tägliche Erinnerung deaktivieren", callback_data="train_time_none")
    ])

    markup = InlineKeyboardMarkup(inline_keyboard=time_buttons)
    await callback.message.edit_text("⏰ Wähle deine tägliche Trainingszeit:", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("train_time_"))
async def handle_selected_time(callback: CallbackQuery, state: FSMContext):
    time_value = callback.data.replace("train_time_", "")
    session = SessionLocal()
    user_settings = session.query(UserSettings).filter_by(user_id=callback.from_user.id).first()

    if time_value == "none":
        if user_settings:
            user_settings.training_time = None
            session.commit()
        await callback.message.edit_text("🛑 Die tägliche Erinnerung wurde deaktiviert.\n\n🔁 Starte dein Training mit /start_training")
    else:
        parsed_time = datetime.strptime(time_value, "%H:%M").time()
        if not user_settings:
            user_settings = UserSettings(user_id=callback.from_user.id, training_time=parsed_time)
            session.add(user_settings)
        else:
            user_settings.training_time = parsed_time
        session.commit()
        await callback.message.edit_text(f"✅ Tägliche Trainingszeit: {time_value} Uhr\n\n🔁 Starte dein Training mit /start_training")

    session.close()
    await state.clear()


@router.callback_query(lambda c: c.data == "setting_num_choices")
async def handle_setting_num_choices(callback: CallbackQuery):
    buttons = [InlineKeyboardButton(text=str(opt.value), callback_data=f"num_opt_{opt.value}") for opt in
               AnswerOptionsCount]
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await callback.message.edit_text("🔢 Wähle, wie viele Antwortoptionen du möchtest:", reply_markup=markup)


@router.callback_query(lambda c: c.data.startswith("num_opt_"))
async def set_user_answer_option(callback: CallbackQuery):
    value = int(callback.data.split("_")[-1])
    session = SessionLocal()
    user_settings = session.query(UserSettings).filter_by(user_id=callback.from_user.id).first()

    if not user_settings:
        user_settings = UserSettings(user_id=callback.from_user.id, answers_count=value)
        session.add(user_settings)
    else:
        user_settings.answers_count = value

    session.commit()
    session.close()

    await callback.message.edit_text(
        f"✅ Ab jetzt bekommst du {value} Antwortoptionen in deinen Trainings.\n\n🔁 Starte dein Training mit /start_training"
    )


@router.callback_query(lambda c: c.data.startswith("setting_") and c.data != "setting_num_choices")
async def handle_settings_stub(callback: CallbackQuery):
    await callback.answer("⚙️ Diese Einstellung ist noch nicht verfügbar.", show_alert=True)

@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    """
    Sends info message with developer contact for feedback, suggestions, or bug reports.
    """
    developer_link = "https://t.me/romavesna"
    text = (
        "💬 <b>Feedback und Vorschläge</b>\n\n"
        "Wenn du Vorschläge, Fragen oder einen Fehler melden möchtest, "
        f"kannst du mir direkt schreiben:\n\n"
        f"👉 <a href=\"{developer_link}\">@romavesna</a>\n\n"
        "Du kannst dabei auch <b>Screenshots</b> oder <b>Dokumente</b> anhängen, "
        "wenn sie beim Beschreiben des Problems helfen.\n\n"
        "Ich freue mich über dein Feedback! 😊"
    )
    await message.answer(text, parse_mode="HTML")


# # Delete any non-text messages silently
# @router.message(F.photo | F.video | F.document | F.sticker | F.voice | F.audio | F.video_note | F.animation)
# async def delete_media(message: Message):
#     try:
#         await message.delete()
#     except Exception as e:
#         # Optional: log error in console if bot lacks rights
#         print(f"Failed to delete media message: {e}")