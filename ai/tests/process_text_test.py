import pytest
from unittest.mock import patch, AsyncMock
from ai.process_text import ask_agent


@pytest.mark.asyncio
@patch("ai.process_text.agent.ainvoke", new_callable=AsyncMock)
async def test_ask_agent(mock_ainvoke):
    class FakeMessageContent:
        def __init__(self, text):
            self.content = [{'text': text}]

    mock_ainvoke.return_value = {'messages': [FakeMessageContent("Тестовый ответ от ИИ")]}

    result = await ask_agent("Привет")

    assert result == "Тестовый ответ от ИИ"
    mock_ainvoke.assert_called_once_with({"messages": [{"role": "user", "content": "Привет"}]})