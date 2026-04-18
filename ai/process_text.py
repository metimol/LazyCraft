from ai.config import agent


async def ask_agent(text: str) -> str:
    response = await agent.ainvoke({"messages": [{"role": "user", "content": text}]})
    ai_message = response["messages"][-1]

    if isinstance(ai_message.content, str):
        return ai_message.content

    if isinstance(ai_message.content, list):
        for item in reversed(ai_message.content):
            if isinstance(item, dict) and "text" in item:
                return item["text"]

    return str(ai_message.content)
