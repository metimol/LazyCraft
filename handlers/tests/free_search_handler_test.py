import pytest
from unittest.mock import patch, AsyncMock
from handlers.free_search_handler import manual_free_check


@pytest.mark.asyncio
@patch("handlers.free_search_handler.split_message")
@patch("handlers.free_search_handler.filter_items_with_llm", new_callable=AsyncMock)
@patch("handlers.free_search_handler.scrape_all_pages", new_callable=AsyncMock)
@patch("handlers.free_search_handler.get_user_prompt", new_callable=AsyncMock)
@patch("handlers.free_search_handler.get_user_radius", new_callable=AsyncMock)
async def test_manual_free_check(
    mock_radius, mock_prompt, mock_scrape, mock_filter, mock_split
):
    mock_msg = AsyncMock()
    mock_status = AsyncMock()
    mock_msg.answer.return_value = mock_status
    mock_msg.from_user.id = 123

    mock_radius.return_value = 10
    mock_prompt.return_value = "Тестовый промпт"
    mock_scrape.return_value = [{"title": "Стол"}]
    mock_filter.return_value = "Ответ от LLM"

    async def fake_split():
        yield "Ответ от LLM"

    mock_split.return_value = fake_split()

    await manual_free_check(mock_msg)

    mock_radius.assert_called_once_with(123)
    mock_prompt.assert_called_once_with(123)
    mock_scrape.assert_called_once()
    mock_filter.assert_called_once_with([{"title": "Стол"}], "Тестовый промпт", 10)
    mock_status.delete.assert_called_once()
    assert mock_msg.answer.call_count == 2
