from ai.config import agent

async def ask_agent(text: str) -> str:
    response = await agent.ainvoke(
        {"messages": [{"role": "user", "content": text}]}
    )

    ai_message = response['messages'][-1]

    if isinstance(ai_message.content, list):
        answer_text = ai_message.content[0]['text']
    else:
        answer_text = ai_message.content

    return answer_text