from ai import ask_agent
from const import locale


async def filter_items_with_llm(items: list, user_prompt: str, radius: int) -> str:
    if not items:
        return locale("nothing_found")

    items_text = ""
    for i in items:
        if isinstance(i, dict):
            title = i.get("title", "")
            distance = i.get("distance", "")
            link = i.get("link", "") or i.get("url", "")
        else:
            title = getattr(i, "title", "")
            distance = getattr(i, "city", getattr(i, "distance", ""))
            link = getattr(i, "url", getattr(i, "link", ""))

        line = f"{title} | Расстояние: {distance} | Ссылка: {link}\n"
        if len(items_text) + len(line) > 600000:
            break
        items_text += line

    sys_msg = locale("check_free_items").format(
        radius=radius, prompt=user_prompt, items=items_text
    )
    resp = await ask_agent(sys_msg)

    return resp
