import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from aiogram import Bot
from utils.scheduler_jobs import scheduled_free_check, update_user_job

@pytest.mark.asyncio
@patch("utils.scheduler_jobs.get_user_radius", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.get_user_prompt", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.scrape_all_pages", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.filter_items_with_llm", new_callable=AsyncMock)
async def test_scheduled_free_check_found(mock_filter, mock_scrape, mock_prompt, mock_radius):
    bot_mock = AsyncMock(spec=Bot)
    mock_radius.return_value = 10
    mock_prompt.return_value = "Запрос"
    mock_scrape.return_value = [{"title": "Вещь 1"}]
    mock_filter.return_value = "Ответ от нейросети"

    await scheduled_free_check(bot_mock, 123)

    mock_radius.assert_called_once_with(123)
    mock_prompt.assert_called_once_with(123)
    mock_scrape.assert_called_once_with(radius=10, query="", max_price=0)
    mock_filter.assert_called_once_with([{"title": "Вещь 1"}], "Запрос", 10)
    bot_mock.send_message.assert_called_once_with(chat_id=123, text="Ответ от нейросети")

@pytest.mark.asyncio
@patch("utils.scheduler_jobs.get_user_radius", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.get_user_prompt", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.scrape_all_pages", new_callable=AsyncMock)
@patch("utils.scheduler_jobs.filter_items_with_llm", new_callable=AsyncMock)
async def test_scheduled_free_check_not_found(mock_filter, mock_scrape, mock_prompt, mock_radius):
    bot_mock = AsyncMock(spec=Bot)
    mock_radius.return_value = 10
    mock_prompt.return_value = "Запрос"
    mock_scrape.return_value = []
    mock_filter.return_value = "сегодня пусто"

    await scheduled_free_check(bot_mock, 123)
    bot_mock.send_message.assert_not_called()

@patch("utils.scheduler_jobs.scheduler")
def test_update_user_job_remove_and_add(mock_scheduler):
    bot_mock = MagicMock(spec=Bot)
    mock_scheduler.get_job.return_value = True

    update_user_job(bot_mock, 123, 6)

    mock_scheduler.get_job.assert_called_with("free_check_123")
    mock_scheduler.remove_job.assert_called_with("free_check_123")
    mock_scheduler.add_job.assert_called_once()

@patch("utils.scheduler_jobs.scheduler")
def test_update_user_job_turn_off(mock_scheduler):
    bot_mock = MagicMock(spec=Bot)
    mock_scheduler.get_job.return_value = False

    update_user_job(bot_mock, 123, 0)

    mock_scheduler.remove_job.assert_not_called()
    mock_scheduler.add_job.assert_not_called()