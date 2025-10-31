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

    async def on_user_message(self, message):
        raise NotImplementedError

    async def on_system_message(self, message):
        raise NotImplementedError

    async def reset_history():
        raise NotImplementedError


class LangChainAdapter(BaseAdapter):
    def __init__(self, cl, config):
        super().__init__(cl, config)

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

    def get_user(self):
        return self.cl.user_session.get("user")

    def get_project(self):
        return self.cl.user_session.get("project")

    def get_history(self, project):
        return self.cl.user_session.get("history", {}).get(project, [])

    def set_history(self, project, project_history):
        # get the whole history dict and update the history for this project
        history = self.cl.user_session.get("history", {})
        history.update({
            project: project_history
        })

        # update the history dict in the session
        self.cl.user_session.set("history", history)

        # update the history dict in the store
        memory_store[self.get_user().identifier] = history

    async def on_chat_start(self):
        history = memory_store.get(self.get_user().identifier, {})
        self.cl.user_session.set("history", history)

    async def on_user_message(self, message, context, stream=False):
        project = context.get("id")
        history = self.get_history(project)

        inputs = {
            "system_prompt": self.config.SYSTEM_PROMPT.format(user=self.get_user().display_name),
            "context": json.dumps(context),
            "history": self.get_history(project),
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
        self.set_history(project, [
            *history,
            HumanMessage(content=message.content),
            AIMessage(content=response_message.content)
        ])

        return response_message

    async def on_system_message(self, message):
        try:
            action = message.metadata.get("action")
            project = message.metadata.get("project")
        except AttributeError:
            action = message.get("metadata", {}).get("action")
            project = None

        if action == "reset_history":
            self.set_history(project, [])


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
