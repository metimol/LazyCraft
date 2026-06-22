from langchain.tools import tool
from kleinanzeigen_api.client import KleinanzeigenAPI
from ai.context import current_message
from const import locale
from database.users import get_user_zip
from utils.geocoding import get_lat_lon, calculate_distance


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

    zip_code = await get_user_zip(msg.from_user.id)
    if not zip_code:
        return locale("missing_zip_code")

    status_msg = await msg.answer(locale("SEARCHING_WITH_QUERY").format(query=query))

    user_coords = await get_lat_lon(zip_code)

    try:
        async with KleinanzeigenAPI() as api:
            total, results = await api.search_page(
                q=query,
                location_id=zip_code,
                max_price=max_price,
                distance_km=radius,
                size=20,
            )

        markdown_table = (
            "| Name | Price | Distance (km) | URL |\n| --- | --- | --- | --- |\n"
        )

        for item in results:
            dist_str = "N/A"
            if user_coords and item.latitude and item.longitude:
                dist = calculate_distance(
                    user_coords[0], user_coords[1], item.latitude, item.longitude
                )
                dist_str = f"{dist:.1f}"

            markdown_table += f"| {item.title} | {item.price} {item.price_type} | {dist_str} | {item.url} |\n"

    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

    if not results:
        return locale("fs_no_results")

    return markdown_table


@tool
async def get_free_items(radius: int):
    """
    Get all free items from Kleinanzeigen.de without search query

    This function return Markdown table with free items (item name, distance from user, url).

    Radius should be integer and can be only 5, 10, 20, 30, 50, 100, 150 or 200
    """

    if radius not in [5, 10, 20, 30, 50, 100, 150, 200]:
        raise ValueError("Radius should be one of 5, 10, 20, 30, 50, 100, 150 or 200")

    msg = current_message.get()

    zip_code = await get_user_zip(msg.from_user.id)
    if not zip_code:
        return locale("missing_zip_code")

    status_msg = await msg.answer(locale("SEARCHING_ZU_VERSHENKEN"))

    user_coords = await get_lat_lon(zip_code)

    try:
        async with KleinanzeigenAPI() as api:
            # max_price=0 usually implies "Verschenken" on Kleinanzeigen if sorted/filtered properly.
            total, results = await api.search_page(
                q="", location_id=zip_code, max_price=0, distance_km=radius, size=20
            )

        markdown_table = "| Name | Distance (km) | URL |\n| --- | --- | --- |\n"

        for item in results:
            dist_str = "N/A"
            if user_coords and item.latitude and item.longitude:
                dist = calculate_distance(
                    user_coords[0], user_coords[1], item.latitude, item.longitude
                )
                dist_str = f"{dist:.1f}"

            markdown_table += f"| {item.title} | {dist_str} | {item.url} |\n"

    finally:
        try:
            await status_msg.delete()
        except Exception:
            pass

    if not results:
        return locale("fs_no_results")

    return markdown_table
