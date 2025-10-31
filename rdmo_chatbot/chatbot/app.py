import chainlit as cl
from utils import get_adapter, get_config, get_user

config = get_config()
adapter = get_adapter(cl, config)


@cl.header_auth_callback
def header_auth_callback(headers):
    return get_user(config, headers)


@cl.on_chat_start
async def on_chat_start():
    await adapter.on_chat_start()


@cl.on_chat_end
async def on_chat_end():
    await adapter.on_chat_end()


@cl.on_chat_resume
async def on_chat_resume(thread):
    await adapter.on_chat_resume(thread)


@cl.on_message
async def on_message(message):
    if message.type == "system_message":
        await adapter.on_system_message(message)
    else:
        context = {}
        if cl.context.session.client_type == "copilot":
            context = await cl.CopilotFunction(name="getContext", args={}).acall()

        response_message = await adapter.on_user_message(message, context, stream=True)
        response_message.actions = [
            cl.Action(name="transfer", icon="file-output", payload={
                "content": response_message.content
            })
        ]
        await response_message.update()


@cl.on_window_message
async def on_window_message(message):
    await adapter.on_system_message(message)


@cl.action_callback("transfer")
async def on_transfer(action):
    inputs = {}
    if cl.context.session.client_type == "copilot":
        inputs = await cl.CopilotFunction(name="getInputs", args={}).acall()

    element = cl.CustomElement(
        name="InputSelect",
        display="inline",
        props={
            "inputs": inputs
        }
    )

    ask_message = cl.AskElementMessage(
        content="Where should I add the content?",
        element=element,
        timeout=60
    )

    ask_response = await ask_message.send()
    ask_response.update(action.payload)

    if ask_response and ask_response.get("submitted"):
        if cl.context.session.client_type == "copilot":
            await cl.CopilotFunction(name="setInput", args=ask_response).acall()


@cl.on_logout
async def on_logout(request, response):
    response.delete_cookie("chatbot_token")


@cl.set_starters
async def set_starters():
    return [cl.Starter(**starter) for starter in config.STARTERS]
