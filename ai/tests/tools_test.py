import pytest
from unittest.mock import patch, AsyncMock
from ai.tools import search_in_kleinanzeigen, get_free_items
from ai.context import current_message


@pytest.mark.asyncio
@patch("ai.tools.scrape_all_pages", new_callable=AsyncMock)
async def test_get_free_items_success(mock_scrape):
    mock_msg = AsyncMock()
    mock_status = AsyncMock()
    mock_msg.answer.return_value = mock_status
    current_message.set(mock_msg)

    mock_scrape.return_value = [
        {"title": "Диван", "distance": "5 км", "link": "http://divan"}
    ]

    result = await get_free_items.ainvoke({"radius": 10})

    assert "Диван" in result
    assert "5 км" in result
    assert "http://divan" in result
    mock_msg.answer.assert_called_once()
    mock_status.delete.assert_called_once()


@pytest.mark.asyncio
async def test_get_free_items_invalid_radius():
    with pytest.raises(ValueError):
        await get_free_items.ainvoke({"radius": 15})


@pytest.mark.asyncio
@patch("ai.tools.scrape_all_pages", new_callable=AsyncMock)
async def test_search_in_kleinanzeigen_success(mock_scrape):
    mock_msg = AsyncMock()
    mock_status = AsyncMock()
    mock_msg.answer.return_value = mock_status
    current_message.set(mock_msg)

    mock_scrape.return_value = [
        {"title": "Велосипед", "price": "50 €", "distance": "10 км", "link": "http://bike"}
    ]

    result = await search_in_kleinanzeigen.ainvoke({"query": "Fahrrad", "radius": 20, "max_price": 100})

    assert "Велосипед" in result
    assert "50 €" in result
    mock_msg.answer.assert_called_once()
    mock_status.delete.assert_called_once()


@pytest.mark.asyncio
async def test_search_in_kleinanzeigen_invalid_args():
    with pytest.raises(ValueError):
        await search_in_kleinanzeigen.ainvoke({"query": "Fahrrad", "radius": 15, "max_price": 100})

    with pytest.raises(ValueError):
        await search_in_kleinanzeigen.ainvoke({"query": "Fahrrad", "radius": 10, "max_price": 600})

    with pytest.raises(ValueError):
        await search_in_kleinanzeigen.ainvoke({"query": "A" * 35, "radius": 10, "max_price": 100})