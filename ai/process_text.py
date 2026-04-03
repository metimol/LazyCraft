from ai.config import agent

async def ask_agent(text: str) -> str:
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": text}]}
    )

    ai_message = response['messages'][-1]
    answer_text = ai_message.content[-1]['text']

    return answer_text