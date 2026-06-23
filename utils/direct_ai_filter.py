from ai import ask_agent
from const import locale


async def filter_items_with_llm(items: list, user_prompt: str) -> str:
    if not items:
        return "none"

    items_text = ""
    for i in items:
        if isinstance(i, dict):
            title = i.get("title", "")
            link = i.get("link", "") or i.get("url", "")
        else:
            title = getattr(i, "title", "")
            link = getattr(i, "url", getattr(i, "link", ""))

        line = f"{title} | URL: {link}\n"
        if len(items_text) + len(line) > 600000:
            break
        items_text += line

    sys_msg = locale("filter_items_with_llm").format(
        prompt=user_prompt, items=items_text
    )
    resp = await ask_agent(sys_msg)

    return resp
