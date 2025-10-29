import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, InlineKeyboardMarkup

from app.db.models import Category, UserCategoryStat
from app.handlers.user import cmd_bot_settings


@pytest.mark.asyncio
async def test_cmd_bot_settings():
    # Create a mock Message object
    mock_message = AsyncMock(spec=Message)

    # Ensure `answer` is an async method (so it can be awaited)
    mock_message.answer = AsyncMock()

    # Call the command handler
    await cmd_bot_settings(mock_message)

    # Assert that `answer` was called exactly once
    mock_message.answer.assert_called_once()

    # Extract the arguments that were passed to message.answer()
    args, kwargs = mock_message.answer.call_args

    # Check that the message text is correct
    assert "🛠️ Wähle deine Einstellungen" in args[0]

    # Get the markup that was sent
    markup: InlineKeyboardMarkup = kwargs["reply_markup"]

    # Verify that the markup is an inline keyboard with one button
    assert isinstance(markup, InlineKeyboardMarkup)
    assert len(markup.inline_keyboard) == 1

    # Check the button’s text and callback data
    button = markup.inline_keyboard[0][0]
    assert button.text == "🔢 Antwortanzahl"
    assert button.callback_data == "setting_num_choices"



@pytest.mark.asyncio
@patch("app.handlers.user.SessionLocal")
async def test_cmd_statistics_no_stats(mock_session_local):
    # Step 1: Mock Message
    mock_message = AsyncMock()
    mock_message.from_user.id = 123
    mock_message.answer = AsyncMock()

    # Step 2: Mock SQLAlchemy Session
    mock_session = MagicMock()
    mock_session.query.return_value.filter_by.return_value.all.return_value = []

    # Step 3: Replace SessionLocal with our mock session
    mock_session_local.return_value = mock_session

    # Step 4: Run the handler
    from app.handlers.user import cmd_statistics
    await cmd_statistics(mock_message)

    # Step 5: Assert the bot responded with the correct message
    mock_message.answer.assert_called_once_with("📊 Du hast noch keine Trainingsstatistiken.")


@pytest.mark.asyncio
@patch("app.handlers.user.SessionLocal")
async def test_cmd_statistics_with_stats(mock_session_local):
    # Step 1: Mock Message
    mock_message = AsyncMock()
    mock_message.from_user.id = 123
    mock_message.answer = AsyncMock()

    # Step 2: Fake DB objects
    fake_stat = UserCategoryStat(
        user_id=123,
        category_id=1,
        correct_attempts=8,
        total_attempts=10
    )
    fake_category = Category(id=1, name="Vocabulary")

    # Step 3: Create mock session
    mock_session = MagicMock()

    # Mock query() so it behaves differently for each model
    def mock_query(model):
        if model == UserCategoryStat:
            # This query uses filter_by(...).all()
            mock_qs = MagicMock()
            mock_qs.filter_by.return_value.all.return_value = [fake_stat]
            return mock_qs
        elif model == Category:
            # This query uses filter(...).all()
            mock_qs = MagicMock()
            mock_qs.filter.return_value.all.return_value = [fake_category]
            return mock_qs
        else:
            return MagicMock()

    mock_session.query.side_effect = mock_query
    mock_session_local.return_value = mock_session

    # Step 4: Run handler
    from app.handlers.user import cmd_statistics
    await cmd_statistics(mock_message)

    # Step 5: Verify message content
    args, kwargs = mock_message.answer.call_args
    text_sent = args[0]

    # Check that category name and stats appear correctly
    assert "🏷️ <b>Vocabulary</b> — <b>80%</b> (8/10)" in text_sent
    assert "🧮 <b>Gesamt</b> — <b>80%</b> (8/10)" in text_sent
    assert kwargs.get("parse_mode") == "HTML"