import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from handlers.settings_handler import (
    settings_cmd,
    process_set_prompt,
    save_prompt,
    process_set_timer,
    save_timer,
    process_set_radius,
    save_radius,
    PromptState,
)


@pytest.mark.asyncio
async def test_settings_cmd():
    mock_msg = AsyncMock()
    await settings_cmd(mock_msg)
    mock_msg.answer.assert_called_once()


@pytest.mark.asyncio
async def test_process_set_prompt():
    mock_callback = AsyncMock()
    mock_state = AsyncMock()

    await process_set_prompt(mock_callback, mock_state)

    mock_callback.message.edit_text.assert_called_once()
    mock_state.set_state.assert_called_once_with(PromptState.waiting_for_prompt)


@pytest.mark.asyncio
@patch("handlers.settings_handler.set_user_prompt", new_callable=AsyncMock)
async def test_save_prompt(mock_set_prompt):
    mock_msg = AsyncMock()
    mock_msg.from_user.id = 123
    mock_msg.text = "Мои новые интересы"
    mock_state = AsyncMock()

    await save_prompt(mock_msg, mock_state)

    mock_set_prompt.assert_called_once_with(123, "Мои новые интересы")
    mock_msg.answer.assert_called_once()
    mock_state.clear.assert_called_once()


@pytest.mark.asyncio
async def test_process_set_timer():
    mock_callback = AsyncMock()
    await process_set_timer(mock_callback)
    mock_callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.settings_handler.set_user_timer", new_callable=AsyncMock)
@patch("handlers.settings_handler.update_user_job")
async def test_save_timer(mock_update_job, mock_set_timer):
    mock_callback = AsyncMock()
    mock_callback.data = "timer_6"
    mock_callback.from_user.id = 123
    mock_bot = MagicMock()

    await save_timer(mock_callback, mock_bot)

    mock_set_timer.assert_called_once_with(123, 6)
    mock_update_job.assert_called_once_with(mock_bot, 123, 6)
    mock_callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
async def test_process_set_radius():
    mock_callback = AsyncMock()
    await process_set_radius(mock_callback)
    mock_callback.message.edit_text.assert_called_once()


@pytest.mark.asyncio
@patch("handlers.settings_handler.set_user_radius", new_callable=AsyncMock)
async def test_save_radius(mock_set_radius):
    mock_callback = AsyncMock()
    mock_callback.data = "radius_20"
    mock_callback.from_user.id = 123

    await save_radius(mock_callback)

    mock_set_radius.assert_called_once_with(123, 20)
    mock_callback.message.edit_text.assert_called_once()
