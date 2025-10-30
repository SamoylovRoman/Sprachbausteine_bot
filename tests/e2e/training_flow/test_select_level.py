import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.handlers.user import handle_level_selection


@pytest.mark.asyncio
async def test_e2e_select_level():
    """
    Simulates a user selecting a training level via inline button (callback query).
    Verifies that the bot proceeds to ask for the number of questions.
    """

    # Step 1: Mock CallbackQuery object
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.data = "train_level_1"  # Correct format for handler
    mock_callback.from_user = MagicMock()
    mock_callback.from_user.id = 123456
    mock_callback.message = AsyncMock()
    mock_callback.message.chat.id = 123456
    mock_callback.message.message_id = 1
    mock_callback.message.answer = AsyncMock()
    mock_callback.message.delete = AsyncMock()
    mock_callback.answer = AsyncMock()

    # Step 2: Mock FSMContext
    mock_state = AsyncMock(spec=FSMContext)
    mock_state.set_data = AsyncMock()
    mock_state.set_state = AsyncMock()

    # Step 3: Call the level selection handler
    await handle_level_selection(callback=mock_callback, state=mock_state)

    # Step 4: Verify that bot asks for number of questions
    mock_callback.message.answer.assert_called()
    response_text = mock_callback.message.answer.call_args[0][0]

    assert "wie viele" in response_text.lower()
