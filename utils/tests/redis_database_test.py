import pytest
from unittest.mock import patch, AsyncMock
from utils.redis_database import (
    get_user_prompt,
    set_user_prompt,
    get_user_radius,
    set_user_radius,
    get_user_timer,
    set_user_timer,
)


@pytest.mark.asyncio
@patch("utils.redis_database.r.get", new_callable=AsyncMock)
async def test_get_user_prompt_exists(mock_get):
    mock_get.return_value = "Тестовый промпт"
    res = await get_user_prompt(1)
    assert res == "Тестовый промпт"
    mock_get.assert_called_once_with("lazy:prompt:1")


@pytest.mark.asyncio
@patch("utils.redis_database.r.get", new_callable=AsyncMock)
@patch("utils.redis_database.DEFAULT_SEARCH_PROMPT", "Дефолтный промпт")
async def test_get_user_prompt_default(mock_get):
    mock_get.return_value = None
    res = await get_user_prompt(1)
    assert res == "Дефолтный промпт"


@pytest.mark.asyncio
@patch("utils.redis_database.r.set", new_callable=AsyncMock)
async def test_set_user_prompt(mock_set):
    await set_user_prompt(1, "Новый промпт")
    mock_set.assert_called_once_with("lazy:prompt:1", "Новый промпт")


@pytest.mark.asyncio
@patch("utils.redis_database.r.get", new_callable=AsyncMock)
async def test_get_user_radius(mock_get):
    mock_get.return_value = "15"
    res = await get_user_radius(2)
    assert res == 15


@pytest.mark.asyncio
@patch("utils.redis_database.r.set", new_callable=AsyncMock)
async def test_set_user_radius(mock_set):
    await set_user_radius(2, 20)
    mock_set.assert_called_once_with("lazy:radius:2", 20)


@pytest.mark.asyncio
@patch("utils.redis_database.r.get", new_callable=AsyncMock)
async def test_get_user_timer(mock_get):
    mock_get.return_value = "12"
    res = await get_user_timer(3)
    assert res == 12


@pytest.mark.asyncio
@patch("utils.redis_database.r.set", new_callable=AsyncMock)
async def test_set_user_timer(mock_set):
    await set_user_timer(3, 24)
    mock_set.assert_called_once_with("lazy:timer:3", 24)
