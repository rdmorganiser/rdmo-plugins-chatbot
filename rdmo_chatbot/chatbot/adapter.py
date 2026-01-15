import json

import chainlit as cl
from langchain_core.messages import AIMessage, AIMessageChunk, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from utils import get_config, get_store, messages_to_dicts

config = get_config()
store = get_store(config)


class BaseAdapter:

    async def call_copilot(self, name: str, default=None, **kwargs):
        if cl.context.session.client_type != "copilot":
            return default

        result = await cl.CopilotFunction(name=name, args=kwargs).acall()

        return default if result is None else result

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
    def __init__(self, *args):
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

    async def on_chat_start(self):
        # get the user from the session
        user = cl.user_session.get("user")

        # get project_id from the copilot and store it in the session
        project_id = await self.call_copilot("getProjectId")
        cl.user_session.set("project_id", project_id)

        # get lang_code from the copilot and store it in the session
        lang_code = await self.call_copilot("getLangCode", default="en")
        cl.user_session.set("lang_code", lang_code)

        # check if we have a history, yet
        if store.has_history(user.identifier, project_id):
            content = getattr(config, f"CONTINUATION_{lang_code.upper()}", "")
            await cl.Message(content=content).send()
            history = store.get_history(user.identifier, project_id)
            await self.send_history(history, user)
        else:
            # if the history is empty, display the confirmation message
            content = getattr(config, f"CONFIRMATION_{lang_code.upper()}", "")
            message = cl.AskActionMessage(content=content, actions=[
                cl.Action(name="confirmation", icon="check", label="", payload={"value": "confirmation"}),
                cl.Action(name="leave", icon="x", label="", payload={"value": "leave"}),
            ])
            response = await message.send()
            await message.remove()

            if response and response.get("payload").get("value") == "confirmation":
                content = getattr(config, f"START_{lang_code.upper()}", "").strip()
                store.set_history(user.identifier, project_id, [
                    AIMessage(content=content)
                ])
                await cl.Message(content=content).send()
            else:
                await self.call_copilot("toggleCopilot")

    async def on_user_message(self, message):
        # get the user from the session
        user = cl.user_session.get("user")

        # get the full project from the copilot
        project = await self.call_copilot("getProject")
        project = project if isinstance(project, dict) else {}
        project_id = project.get("id")

        # get the history from the store
        history = store.get_history(user.identifier, project_id)

        # collect inputs for the llm
        inputs = {
            "system_prompt": config.SYSTEM_PROMPT.format(user=user.display_name),
            "context": json.dumps(project),
            "history": history,
            "content": message.content
        }

        # send an initial empty response
        response_message = await cl.Message(content="").send()

        # stream from or invoke the chain
        if config.STREAM:
            async for chunk in self.chain.astream(inputs):
                if isinstance(chunk, AIMessageChunk):
                    await response_message.stream_token(chunk.content)
        else:
            response = await self.chain.ainvoke(inputs)
            response_message.content = response.content

        # add the transfer action
        response_message.actions = [
            cl.Action(name="on_transfer", icon="file-output", payload={
                "content": response_message.content
            }),
            cl.Action(name="on_contact", icon="mail", payload={
                "history": messages_to_dicts(history)
            })
        ]

        # update the message
        await response_message.update()

        # add messages to history and store
        store.set_history(user.identifier, project_id, [
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
            user = cl.user_session.get("user")
            project_id = cl.user_session.get("project_id")
            store.reset_history(user.identifier, project_id)

    async def on_transfer(self, action):
        await self.call_copilot("handleTransfer", **action.payload)

    async def on_contact(self, action):
        # get user and project_id from the session
        user = cl.user_session.get("user")
        project_id = cl.user_session.get("project_id")

        # get the history from the store
        history = store.get_history(user.identifier, project_id)

        await self.call_copilot("openContactModal", history=messages_to_dicts(history))

    async def send_history(self, history, user):
        for message in history:
            if isinstance(message, HumanMessage):
                message_author = user.display_name or "You"
                message_type = "user_message"
            elif isinstance(message, AIMessage):
                message_author = config.ASSISTANT_NAME
                message_type = "assistant_message"
            else:
                continue

            await cl.Message(content=message.content, author=message_author, type=message_type).send()

class OpenAILangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(**config.LLM_ARGS)


class OllamaLangChainAdapter(LangChainAdapter):

    @property
    def llm(self):
        from langchain_ollama import ChatOllama
        return ChatOllama(**config.LLM_ARGS)
