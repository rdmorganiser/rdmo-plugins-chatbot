from openai import AsyncOpenAI

from . import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    def __init__(self, cl, config):
        self.cl = cl
        self.cl.instrument_openai()
        self.config = config

        self.client = AsyncOpenAI(
            base_url=config.OPENAI_BASE_URL,
            api_key=config.OPENAI_API_KEY,
        )

    async def on_message(self, message):
        messages = [
            {
                "role": "system", "content": self.config.SYSTEM_PROMPT
            },
            *self.cl.chat_context.to_openai(),
        ]

        response = await self.client.chat.completions.create(
            messages=messages, **self.config.OPENAI_ARGS
        )

        await self.cl.Message(content=response.choices[0].message.content).send()
