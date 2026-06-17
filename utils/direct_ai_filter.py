from ai import ask_agent
from const import locale


async def filter_items_with_llm(items: list, user_prompt: str, radius: int) -> str:
    if not items:
        return locale("nothing_found")

    items_text = ""
    for i in items:
        line = f"{i['title']} | Расстояние: {i['distance']} | Ссылка: {i['link']}\n"
        if len(items_text) + len(line) > 600000:
            break
        items_text += line

    sys_msg = locale("check_free_items").format(
        radius=radius, prompt=user_prompt, items=items_text
    )
    resp = await ask_agent(sys_msg)

    return resp
