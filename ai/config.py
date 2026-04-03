from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from const import GOOGLE_API_KEY, phrases
from ai.tools import search_in_kleinanzeigen, get_free_items

model = init_chat_model(
    model="google_genai:gemma-4-31b-it",
    api_key=GOOGLE_API_KEY
)

agent = create_agent(model, tools=[search_in_kleinanzeigen, get_free_items], system_prompt=phrases.get_value("SYSTEM_PROMPT"), name=phrases.get_value("NAME"))