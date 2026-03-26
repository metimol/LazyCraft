from langchain.tools import tool
from utils.scrape_kleinanzeigen import scrape_all_pages

@tool
async def search_in_kleinanzeigen(query: str, radius: int, max_price: int):
    """
    Get search results from Kleinanzeigen.de.

    This function return Markdown table with search results (item name, item price, distance from user, url).

    Maximal item price should be integer from 0 to 500
    Radius should be integer and can be only 5, 10, 20, 30, 50, 100, 150 or 200
    Query should be less than 30 characters
    """
    if max_price < 0 or max_price > 500:
        raise ValueError("Max price should be between 0 and 500")

    if radius not in [5, 10, 20, 30, 50, 100, 150, 200]:
        raise ValueError("Radius should be one of 5, 10, 20, 30, 50, 100, 150 or 200")

    if len(query)>30:
        raise ValueError("Query should be less than 30 characters")


    items = await scrape_all_pages(radius=radius, query=query, max_price=max_price)
    markdown_table = "| Name | Price | Distance | URL |\n| --- | --- | --- | --- |\n"

    for item in items:
        markdown_table.join(f"| {item['title']} | {item['price']} | {item['distance']} | {item['link']} |\n")

    return markdown_table