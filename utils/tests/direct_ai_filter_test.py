from unittest.mock import patch, AsyncMock
from utils.direct_ai_filter import filter_items_with_llm


@patch("utils.direct_ai_filter.phrases.get_value")
async def test_filter_items_empty_list(mock_get_value):
    mock_get_value.return_value = "Ничего не найдено"
    items = []

    result = await filter_items_with_llm(items, "Найти вещи", 15)

    assert result == "Ничего не найдено"
    mock_get_value.assert_called_once_with("nothing_found")


@patch("utils.direct_ai_filter.ask_agent", new_callable=AsyncMock)
@patch("utils.direct_ai_filter.phrases.get_value")
async def test_filter_items_success(mock_get_value, mock_ask_agent):
    mock_get_value.return_value = "Шаблон: {radius} | {prompt} | {items}"
    mock_ask_agent.return_value = "Ответ от нейросети"
    items = [
        {"title": "Вещь 1", "distance": "5 км", "link": "http://link1"},
        {"title": "Вещь 2", "distance": "12 км", "link": "http://link2"}
    ]

    result = await filter_items_with_llm(items, "Тестовый запрос", 20)

    assert result == "Ответ от нейросети"
    mock_get_value.assert_called_once_with("check_free_items")
    mock_ask_agent.assert_called_once()