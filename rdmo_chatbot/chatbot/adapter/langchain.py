from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables import RunnableMap

from . import BaseAdapter


class LangChainAdapter(BaseAdapter):
    def __init__(self, cl, settings):
        self.cl = cl
        self.settings = settings

        self.chat_history = ChatMessageHistory()

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ]
        )

        self.chain = (
            RunnableMap(
                {
                    "system_prompt": lambda _: cl.user_session.get("system_prompt"),
                    "chat_history": lambda _: self.chat_history.messages,
                    "input": lambda input: input["input"],
                }
            )
            | self.prompt
            | self.llm
        )

    async def on_message(self, message):
        self.chat_history.add_user_message(message.content)
        response = await self.chain.ainvoke({"input": message.content})
        self.chat_history.add_ai_message(response.content)
        await self.cl.Message(content=response.content).send()

    @property
    def llm(self):
        raise NotImplementedError


class OpenAILangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**self.settings.CHAINLIT_LANGCHAIN_SETTINGS)


class OllamaLangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**self.settings.CHAINLIT_LANGCHAIN_SETTINGS)
