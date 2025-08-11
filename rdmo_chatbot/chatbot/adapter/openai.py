from openai import AsyncOpenAI

from . import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    def __init__(self, cl, settings):
        self.cl = cl
        self.cl.instrument_openai()

        self.settings = settings

        self.client = AsyncOpenAI(
            base_url=settings.CHAINLIT_OPENAI_URL,
            api_key=settings.CHAINLIT_OPENAI_API_KEY,
        )

    async def on_message(self, message):
        messages = [
            {"content": self.cl.user_session.get("system_prompt"), "role": "system"},
            *self.cl.chat_context.to_openai(),
        ]

        response = await self.client.chat.completions.create(
            messages=messages, **self.settings.CHAINLIT_OPENAI_SETTINGS
        )

        await self.cl.Message(content=response.choices[0].message.content).send()
