import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

memory_store = {}


class BaseAdapter:
    def __init__(self, cl, config):
        self.cl = cl
        self.config = config

    async def on_chat_start(self):
        pass

    async def on_chat_end(self):
        pass

    async def on_chat_resume(self, thread):
        pass

    async def on_message(self, message):
        raise NotImplementedError


class LangChainAdapter(BaseAdapter):
    def __init__(self, cl, config):
        self.cl = cl
        self.config = config

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                ("system", "{context}"),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{content}")
            ]
        )

        self.chain = self.prompt | self.llm

    @property
    def llm(self):
        raise NotImplementedError

    @property
    def user(self):
        return self.cl.user_session.get("user")

    @property
    def history(self):
        return self.cl.user_session.get("history", [])

    async def on_chat_start(self):
        history = memory_store.get(self.user.identifier, [])
        self.cl.user_session.set("history", history)

    async def on_message(self, message, context, stream=False):
        inputs = {
            "system_prompt": self.config.SYSTEM_PROMPT.format(user=self.user.display_name),
            "context": json.dumps(context),
            "history": self.history,
            "content": message.content
        }

        if stream:
            response_message = await self.cl.Message(content="").send()
            async for chunk in self.chain.astream(inputs):
                if isinstance(chunk, AIMessageChunk):
                    await response_message.stream_token(chunk.content)
            await response_message.update()
        else:
            response = await self.chain.ainvoke(inputs)
            response_message = await self.cl.Message(content=response.content).send()

        # add messages to history
        self.cl.user_session.set("history", [
            *self.history,
            HumanMessage(content=message.content),
            AIMessage(content=response_message.content)
        ])

        # persist memory
        memory_store[self.user.identifier] = self.history

        return response_message


class OpenAILangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**self.config.LLM_ARGS)


class OllamaLangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**self.config.LLM_ARGS)
