from langchain.tools import tool
from utils.scrape_kleinanzeigen import scrape_all_pages
from ai.context import current_message
from const import phrases


@tool
async def search_in_kleinanzeigen(query: str, radius: int, max_price: int):
    """
    Get search results from Kleinanzeigen.de.

    This function return Markdown table with search results (item name, item price, distance from user, url).

    Maximal item price should be integer from 0 to 500
    Radius should be integer and can be only 5, 10, 20, 30, 50, 100, 150 or 200
    Query must be less than 30 characters long and must be in German only.
    """
    if max_price < 0 or max_price > 500:
        raise ValueError("Max price should be between 0 and 500")

    if radius not in [5, 10, 20, 30, 50, 100, 150, 200]:
        raise ValueError("Radius should be one of 5, 10, 20, 30, 50, 100, 150 or 200")

    if len(query) > 30:
        raise ValueError("Query should be less than 30 characters")

    msg = current_message.get()

    status_msg = await msg.answer(phrases.get_value("SEARCHING_WITH_QUERY").format(query=query))

    async def update_progress(page: int, found_count: int):
        try:
            await status_msg.edit_text(
                f"{phrases.get_value('SEARCHING_WITH_QUERY').format(query=query)}\n\n"
                f"{phrases.get_value('CHECKED_PAGES').format(page=page)}\n"
                f"{phrases.get_value('ITEMS_FOUNDED').format(count=found_count)}"
            )
        except Exception:
            pass

    items = await scrape_all_pages(
        radius=radius,
        query=query,
        max_price=max_price,
        progress_callback=update_progress
    )

    try:
        await status_msg.delete()
    except Exception:
        pass

    markdown_table = "| Name | Price | Distance | URL |\n| --- | --- | --- | --- |\n"

    for item in items:
        markdown_table += f"| {item['title']} | {item['price']} | {item['distance']} | {item['link']} |\n"

    return markdown_table

@tool
async def get_free_items(radius: int):
    """
    Get free items from Kleinanzeigen.de.

    This function return Markdown table with free items (item name, distance from user, url).

    Radius should be integer and can be only 5, 10, 20, 30, 50, 100, 150 or 200
    """

    if radius not in [5, 10, 20, 30, 50, 100, 150, 200]:
        raise ValueError("Radius should be one of 5, 10, 20, 30, 50, 100, 150 or 200")

    msg = current_message.get()

    status_msg = await msg.answer(phrases.get_value("SEARCHING_ZU_VERSHENKEN"))

    async def update_progress(page: int, found_count: int):
        try:
            await status_msg.edit_text(
                f"{phrases.get_value('SEARCHING_ZU_VERSHENKEN')}\n\n"
                f"{phrases.get_value('CHECKED_PAGES').format(page=page)}\n"
                f"{phrases.get_value('ITEMS_FOUNDED').format(count=found_count)}"
            )
        except Exception:
            pass

    items = await scrape_all_pages(
        radius=radius,
        query="",
        max_price=0,
        progress_callback=update_progress
    )

    try:
        await status_msg.delete()
    except Exception:
        pass

    markdown_table = "| Name | Distance | URL |\n| --- | --- | --- |\n"

    for item in items:
        markdown_table += f"| {item['title']} | {item['distance']} | {item['link']} |\n"

    return markdown_table