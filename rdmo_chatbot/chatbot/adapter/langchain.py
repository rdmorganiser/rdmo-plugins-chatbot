from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableMap

from . import BaseAdapter


class LangChainAdapter(BaseAdapter):
    def __init__(self, cl, settings):
        self.cl = cl
        self.settings = settings

        self.chat_history = []

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
                    "chat_history": lambda _: self.chat_history,
                    "input": lambda input: input["input"],
                }
            )
            | self.prompt
            | self.llm
        )

    async def on_message(self, message):
        # add user message to chat history
        self.chat_history.append(HumanMessage(content=message.content))

        # invoke llm
        response = await self.chain.ainvoke({"input": message.content})

        # add ai response to chat history
        self.chat_history.append(response)

        # send the response to the user
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
