import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from app.handlers.user import handle_count_selection


@pytest.mark.asyncio
@patch("app.handlers.user.send_example")  # Mock send_example to avoid deep logic
@patch("app.handlers.user.SessionLocal")  # Mock DB session factory
async def test_e2e_select_count(mock_session_local, mock_send_example):
    """
    Simulates user selecting the number of examples (e.g., 5).
    Verifies that the bot sends a confirmation message and calls send_example.
    """

    # Step 1: Mock CallbackQuery
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.data = "train_count_5"
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
    mock_state.get_data = AsyncMock(return_value={
        "level_id": 1,
        "level_name": "A1"
    })
    mock_state.update_data = AsyncMock()

    # Step 3: Mock session query to return 5 example IDs
    mock_session = MagicMock()
    mock_session.query.return_value.join.return_value.filter.return_value.all.return_value = [(1,), (2,), (3,), (4,), (5,)]
    mock_session_local.return_value = mock_session

    # Step 4: Call the handler
    await handle_count_selection(callback=mock_callback, state=mock_state)

    # Step 5: Assert the bot responded correctly
    mock_callback.message.answer.assert_called_once()
    response_text = mock_callback.message.answer.call_args[0][0]

    assert "Niveau: A1" in response_text
    assert "Anzahl der Beispiele: 5" in response_text
    assert "Los geht's" in response_text

    # Step 6: Ensure send_example was called
    mock_send_example.assert_called_once()
