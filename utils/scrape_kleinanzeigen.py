import asyncio
import re
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup


def build_url(location_name: str, location_id: str, radius: int, query: str, max_price: int, page: int) -> str:
    safe_query = query.lower().replace(" ", "-")
    safe_location = location_name.lower().replace(" ", "-")

    if page == 1:
        return f"https://www.kleinanzeigen.de/s-{safe_location}/preis::{max_price}/{safe_query}/k0{location_id}r{radius}"
    return f"https://www.kleinanzeigen.de/s-{safe_location}/preis::{max_price}/seite:{page}/{safe_query}/k0{location_id}r{radius}"


async def fetch_html(session: AsyncSession, url: str) -> str:
    response = await session.get(url)
    if response.status_code == 200:
        return response.text
    return ""


def parse_page(html: str) -> list:
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.find_all('article', class_='aditem')

    for article in articles:
        ad_id = article.get('data-ad-id', '')

        title_tag = article.find('a', class_='ellipsis')
        if not title_tag:
            continue

        title = title_tag.text.strip()
        link = "https://www.kleinanzeigen.de" + title_tag.get('href', '')

        price_tag = article.find('p', class_='aditem-main--middle--price-shipping--price')
        if price_tag:
            price_raw = price_tag.get_text(separator='\n').strip()
            price = re.sub(r'\s+', ' ', price_raw.split('\n')[0].strip())
        else:
            price = "N/A"

        location_tag = article.find('div', class_='aditem-main--top--left')
        distance = "N/A"
        if location_tag:
            location_text = location_tag.text.strip()
            parts = location_text.split('\n')
            for part in parts:
                if 'km' in part:
                    distance = re.sub(r'\s+', ' ', part.strip())
                    break
            if distance == "N/A" and parts:
                distance = re.sub(r'\s+', ' ', parts[-1].strip())

        results.append({
            "id": ad_id,
            "title": title,
            "price": price,
            "distance": distance,
            "link": link,
            "raw_html": str(article)
        })

    return results


async def scrape_all_pages(radius: int, query: str, max_price: int,
                           max_pages: int = 50, location_name: str = "grafenberg", location_id: str = "l11400"):
    all_results = []
    seen_signatures = set()

    async with AsyncSession(impersonate="chrome120") as session:
        for page in range(1, max_pages + 1):
            url = build_url(location_name, location_id, radius, query, max_price, page)
            html = await fetch_html(session, url)

            if not html:
                break

            items = parse_page(html)
            if not items:
                break

            new_items_count = 0
            for item in items:
                signature = (item['title'], item['price'], item['distance'])
                if signature not in seen_signatures:
                    seen_signatures.add(signature)
                    all_results.append(item)
                    new_items_count += 1

            if new_items_count == 0:
                break

            await asyncio.sleep(1)

    return all_results