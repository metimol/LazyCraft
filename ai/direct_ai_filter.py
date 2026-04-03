from langchain.chat_models import init_chat_model
from const import GOOGLE_API_KEY

direct_model = init_chat_model(
    model="google_genai:gemma-4-31b-it",
    api_key=GOOGLE_API_KEY
)

async def filter_items_with_llm(items: list, user_prompt: str) -> str:
    if not items:
        return "Сегодня пусто"

    items_text = "\n".join([f"{i['title']} | Расстояние: {i['distance']} | Ссылка: {i['link']}" for i in items])

    sys_msg = (
        "Ты Lazy, панк-помощник. Пользователь ищет халяву на Kleinanzeigen.\n"
        f"Его интересы: {user_prompt}\n"
        "Вот список найденного:\n"
        f"{items_text}\n"
        "Выбери ТОЛЬКО то, что подходит под интересы. Если ничего подходящего нет, ответь ровно одной фразой: 'Сегодня пусто'. Если есть подходящее — напиши дерзко, с ссылками и укажи расстояние."
    )

    resp = await direct_model.ainvoke([{"role": "user", "content": sys_msg}])
    return resp.content.strip()