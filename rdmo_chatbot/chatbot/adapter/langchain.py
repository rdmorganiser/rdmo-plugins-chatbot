import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from . import BaseAdapter

memory_store = {}

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
            "system_prompt": self.config.SYSTEM_PROMPT,
            "context": json.dumps(context),
            "history": self.history,
            "content": message.content
        }

        response_content = ""
        if stream:
            async for chunk in self.chain.astream(inputs):
                if isinstance(chunk, AIMessageChunk):
                    response_content += chunk.content
                    await self.cl.Message(content=chunk.content).send()
        else:
            response = await self.chain.ainvoke(inputs)
            response_content = response.content
            await self.cl.Message(content=response_content).send()

        # add messages to history
        self.cl.user_session.set("history", [
            *self.history,
            HumanMessage(content=message.content),
            AIMessage(content=response_content)
        ])

        # persist memory
        memory_store[self.user.identifier] = self.history


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
