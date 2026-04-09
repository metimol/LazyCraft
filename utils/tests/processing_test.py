import pytest
from unittest.mock import patch, AsyncMock

from utils.processing import text_processing


@pytest.mark.asyncio
@patch("utils.processing.split_message")
@patch("utils.processing.ask_agent", new_callable=AsyncMock)
@patch("utils.processing.current_message")  # Мокаем сам объект, а не его метод .set
async def test_text_processing(mock_current_message, mock_ask_agent, mock_split_message):
    mock_message = AsyncMock()
    mock_message.text = "Привет, бот!"

    mock_ask_agent.return_value = "Длинный ответ от ИИ"

    async def fake_split():
        yield "Длинный "
        yield "ответ от ИИ"

    mock_split_message.return_value = fake_split()

    await text_processing(mock_message)

    mock_current_message.set.assert_called_once_with(mock_message)
    mock_ask_agent.assert_called_once_with("Привет, бот!")
    mock_split_message.assert_called_once_with("Длинный ответ от ИИ")

    assert mock_message.answer.call_count == 2
    calls = mock_message.answer.call_args_list
    assert calls[0][0][0] == "Длинный "
    assert calls[1][0][0] == "ответ от ИИ"