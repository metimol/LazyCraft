import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message
from bot import (
    AuthMiddleware,
    command_start_handler,
    command_help_handler,
    not_supported_command,
    not_supported_format
)


@pytest.mark.asyncio
@patch("bot.ALLOWED_USERS", [123])
@patch("bot.phrases.get_value")
async def test_auth_middleware_allowed(mock_get_value):
    middleware = AuthMiddleware()
    mock_handler = AsyncMock()

    mock_event = AsyncMock(spec=Message)
    mock_event.from_user = MagicMock()
    mock_event.from_user.id = 123

    await middleware(mock_handler, mock_event, {})

    mock_handler.assert_called_once_with(mock_event, {})
    mock_event.answer.assert_not_called()


@pytest.mark.asyncio
@patch("bot.ALLOWED_USERS", [123])
@patch("bot.phrases.get_value", return_value="Нет доступа")
async def test_auth_middleware_denied(mock_get_value):
    middleware = AuthMiddleware()
    mock_handler = AsyncMock()

    mock_event = AsyncMock(spec=Message)
    mock_event.from_user = MagicMock()
    mock_event.from_user.id = 999

    await middleware(mock_handler, mock_event, {})

    mock_handler.assert_not_called()
    mock_event.answer.assert_called_once_with("Нет доступа")


@pytest.mark.asyncio
@patch("bot.phrases.get_value", return_value="Привет")
@patch("bot.get_main_keyboard", return_value="Клавиатура")
async def test_command_start_handler(mock_keyboard, mock_get_value):
    mock_message = AsyncMock()
    await command_start_handler(mock_message)
    mock_message.answer.assert_called_once_with("Привет", reply_markup="Клавиатура")


@pytest.mark.asyncio
@patch("bot.phrases.get_value", return_value="Помощь")
async def test_command_help_handler(mock_get_value):
    mock_message = AsyncMock()
    await command_help_handler(mock_message)
    mock_message.answer.assert_called_once_with("Помощь")


@pytest.mark.asyncio
@patch("bot.phrases.get_value", return_value="Команда не поддерживается")
async def test_not_supported_command(mock_get_value):
    mock_message = AsyncMock()
    mock_message.text = "/unknown"
    await not_supported_command(mock_message)
    mock_message.answer.assert_called_once_with("Команда не поддерживается")


@pytest.mark.asyncio
@patch("bot.phrases.get_value", return_value="Формат не поддерживается")
async def test_not_supported_format(mock_get_value):
    mock_message = AsyncMock()
    await not_supported_format(mock_message)
    mock_message.answer.assert_called_once_with("Формат не поддерживается")