from ai import ask_agent
from const import phrases


async def filter_items_with_llm(items: list, user_prompt: str, radius: int) -> str:
    if not items:
        return phrases.get_value("nothing_found")

    items_text = "\n".join(
        [
            f"{i['title']} | Расстояние: {i['distance']} | Ссылка: {i['link']}"
            for i in items
        ]
    )

    sys_msg = phrases.get_value("check_free_items").format(
        radius=radius, prompt=user_prompt, items=items_text
    )
    resp = await ask_agent(sys_msg)

    return resp
