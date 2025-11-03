import json

from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

memory_store = {}


class BaseAdapter:
    def __init__(self, cl, config):
        self.cl = cl
        self.config = config

    async def call_copilot(self, name, args={}, default=None):
        return_value = default
        if self.cl.context.session.client_type == "copilot":
            return_value = await self.cl.CopilotFunction(name=name, args=args).acall()
        return return_value

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

    async def on_transfer(self, action):
        pass


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

    def get_history(self):
        return self.cl.user_session.get("history", [])

    def set_history(self, history):
        project_id = self.cl.user_session.get("project_id", None)

        # update the history dict in the session
        self.cl.user_session.set("history", history)

        # update the history dict in the store
        history_store = memory_store.get(self.get_user().identifier, {})
        history_store.update({
            project_id: history
        })
        memory_store[self.get_user().identifier] = history_store

    async def on_chat_start(self):
        project_id = await self.call_copilot("getProjectId")

        history_store = memory_store.get(self.get_user().identifier, {})
        history = history_store.get(project_id , [])

        self.cl.user_session.set("project_id", project_id)
        self.cl.user_session.set("history", history)

        if history:
            await self.cl.Message(content=self.config.CONTINUATION_EN).send()
        else:
            # if the history is empty, display the confirmation message
            message = self.cl.AskActionMessage(content=self.config.CONFIRMATION_EN, actions=[
                self.cl.Action(name="confirmation", icon="check", label="", payload={"value": "confirmation"}),
                self.cl.Action(name="leave", icon="x", label="", payload={"value": "leave"}),
            ])
            response = await message.send()
            await message.remove()

            if response and response.get("payload").get("value") == "confirmation":
                empty_message = self.cl.Message(content="")
                await self.on_user_message(empty_message)
            else:
                await self.call_copilot("toggleCopilot")

    async def on_user_message(self, message):
        project = await self.call_copilot("getProject", default={})
        history = self.get_history()

        inputs = {
            "system_prompt": self.config.SYSTEM_PROMPT.format(user=self.get_user().display_name),
            "context": json.dumps(project),
            "history": history,
            "content": message.content
        }

        # send an initial empty response
        response_message = await self.cl.Message(content="").send()

        # stream from or invoke the chain
        if self.config.STREAM:
            async for chunk in self.chain.astream(inputs):
                if isinstance(chunk, AIMessageChunk):
                    await response_message.stream_token(chunk.content)
        else:
            response = await self.chain.ainvoke(inputs)
            response_message.content = response.content

        # add the transfer action
        response_message.actions = [
            self.cl.Action(name="on_transfer", icon="file-output", payload={
                "content": response_message.content
            })
        ]

        # update the message
        await response_message.update()

        # add messages to history
        self.set_history([
            *history,
            HumanMessage(content=message.content),
            AIMessage(content=response_message.content)
        ])

        return response_message

    async def on_system_message(self, message):
        try:
            action = message.metadata.get("action")
        except AttributeError:
            action = message.get("metadata", {}).get("action")

        if action == "reset_history":
            self.set_history([])

    async def on_transfer(self, action):
        inputs = await self.call_copilot("getInputs", default={})

        element = self.cl.CustomElement(
            name="InputSelect",
            display="inline",
            props={
                "inputs": inputs
            }
        )

        ask_message = self.cl.AskElementMessage(
            content="Where should I add the content?",
            element=element,
            timeout=60
        )

        ask_response = await ask_message.send()
        ask_response.update(action.payload)

        if ask_response and ask_response.get("submitted"):
            await self.call_copilot("setInput", args=ask_response)


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
