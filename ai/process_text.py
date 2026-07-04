import logging

from ai.config import agent
from const import locale

logger = logging.getLogger(__name__)


async def ask_agent(text: str) -> str:
    try:
        msg = {"role": "user", "content": text}
        response = await agent.ainvoke({"messages": [msg]})
    except Exception as e:  # noqa: BLE001
        logger.warning("Error calling AI in ask_agent: %s", e)
        return locale("ai_error")
    ai_message = response["messages"][-1]

    if isinstance(ai_message.content, str):
        return ai_message.content

    if isinstance(ai_message.content, list):
        for item in reversed(ai_message.content):
            if isinstance(item, dict) and "text" in item:
                return item["text"]

    return str(ai_message.content)
