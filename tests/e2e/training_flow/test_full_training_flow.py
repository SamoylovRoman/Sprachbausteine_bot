import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from app.handlers.user import send_example


@pytest.mark.asyncio
async def test_send_example_completion():
    """
    Test that send_example sends a final training summary when all examples are completed.
    """

    # Step 1: Mock Message (from user)
    mock_message = AsyncMock(spec=Message)
    mock_message.answer = AsyncMock()

    # Step 2: Mock FSMContext with last step reached
    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={
        "current_index": 5,
        "example_ids": [1, 2, 3, 4, 5],
        "correct_count": 4,
        "total_count": 5
    })
    mock_state.clear = AsyncMock()

    # Step 3: Call send_example
    await send_example(mock_message, mock_state)

    # Step 4: Check if final message was sent
    mock_message.answer.assert_called_once()
    sent_text = mock_message.answer.call_args[0][0]
    assert "Training abgeschlossen" in sent_text

    # Step 5: FSM state must be cleared
    mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_send_example_completion_callbackquery():
    """
    Test that send_example handles CallbackQuery correctly at training end.
    """

    # Mock CallbackQuery
    mock_callback = AsyncMock(spec=CallbackQuery)
    mock_callback.message = AsyncMock()
    mock_callback.message.answer = AsyncMock()

    # FSMContext with completed state
    mock_state = AsyncMock(spec=FSMContext)
    mock_state.get_data = AsyncMock(return_value={
        "current_index": 5,
        "example_ids": [1, 2, 3, 4, 5],
        "correct_count": 5,
        "total_count": 5
    })
    mock_state.clear = AsyncMock()

    await send_example(mock_callback, mock_state)

    mock_callback.message.answer.assert_called_once()
    sent_text = mock_callback.message.answer.call_args[0][0]
    assert "Training abgeschlossen" in sent_text
    assert "5/5" in sent_text
    assert "/start_training" in sent_text

    mock_state.clear.assert_called_once()
