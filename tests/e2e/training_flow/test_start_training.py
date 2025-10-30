import pytest
from unittest.mock import AsyncMock
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.handlers.user import cmd_training


@pytest.mark.asyncio
async def test_e2e_cmd_training_starts():
    """
    Simulates the start of a training session by calling cmd_training.
    Verifies that the bot prompts the user to select a difficulty level.
    """

    # Step 1: Mock Message object
    mock_message = AsyncMock(spec=Message)
    mock_message.text = "/training"
    mock_message.from_user = AsyncMock()
    mock_message.from_user.id = 123456
    mock_message.answer = AsyncMock()

    # Step 2: Mock FSMContext
    mock_state = AsyncMock(spec=FSMContext)

    # Step 3: Call the handler
    await cmd_training(mock_message, mock_state)

    # Step 4: Check that bot replied with level selection prompt
    mock_message.answer.assert_called()
    response_text = mock_message.answer.call_args[0][0]

    # Updated assertion for German response
    assert "Niveau" in response_text or "möchtest du trainieren" in response_text.lower()
