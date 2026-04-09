import pytest
from unittest.mock import patch, AsyncMock
from utils.scrape_kleinanzeigen import build_url, fetch_html, parse_page, scrape_all_pages


def test_build_url_no_query_page_1():
    url = build_url("Grafenberg", "l11400", 10, "", 0, 1)
    assert url == "https://www.kleinanzeigen.de/s-zu-verschenken-tauschen/grafenberg/c272l11400r10"


def test_build_url_with_query_page_2():
    url = build_url("Stuttgart", "l1234", 20, "laptop", 50, 2)
    assert url == "https://www.kleinanzeigen.de/s-stuttgart/sortierung:preis/preis::50/seite:2/laptop/k0l1234r20"


@pytest.mark.asyncio
async def test_fetch_html_success():
    session_mock = AsyncMock()
    response_mock = AsyncMock()
    response_mock.status_code = 200
    response_mock.text = "<html></html>"
    session_mock.get.return_value = response_mock

    html = await fetch_html(session_mock, "http://test.com")
    assert html == "<html></html>"


def test_parse_page():
    html = """
    <article class="aditem" data-ad-id="12345">
        <div class="aditem-main--top--left">10 km</div>
        <a class="ellipsis" href="/s-anzeige/test/12345">Test Ad</a>
        <p class="aditem-main--middle--price-shipping--price">10 €</p>
    </article>
    """
    items = parse_page(html)
    assert len(items) == 1
    assert items[0]["id"] == "12345"
    assert items[0]["title"] == "Test Ad"
    assert items[0]["price"] == "10 €"
    assert items[0]["distance"] == "10 km"
    assert items[0]["link"] == "https://www.kleinanzeigen.de/s-anzeige/test/12345"


@pytest.mark.asyncio
@patch("utils.scrape_kleinanzeigen.fetch_html", new_callable=AsyncMock)
@patch("utils.scrape_kleinanzeigen.parse_page")
@patch("utils.scrape_kleinanzeigen.AsyncSession")
async def test_scrape_all_pages(mock_session_cls, mock_parse, mock_fetch):
    mock_session = AsyncMock()
    mock_session_cls.return_value.__aenter__.return_value = mock_session

    mock_fetch.side_effect = ["<html>1</html>", "<html>2</html>", ""]
    mock_parse.side_effect = [
        [{"id": "1", "title": "A", "price": "0", "distance": "5", "link": ""}],
        [{"id": "2", "title": "B", "price": "0", "distance": "5", "link": ""}],
        []
    ]

    results = await scrape_all_pages(10, "", 0, max_pages=3)
    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[1]["id"] == "2"