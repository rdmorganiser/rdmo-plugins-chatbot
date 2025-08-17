import chainlit as cl
from utils import get_adapter, get_config, get_user, parse_context

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
    if cl.context.session.client_type == "copilot":
        # call the front end to emit "chainlit-call-fn" and expect a base64 encoded json in return
        raw_context = await cl.CopilotFunction(name="getContext", args={}).acall()
        context = parse_context(raw_context)
    else:
        context = {}

    await adapter.on_message(message, context)


@cl.on_logout
async def on_logout(request, response):
    response.delete_cookie("chatbot_token")


@cl.set_starters
async def set_starters():
    return [cl.Starter(**starter) for starter in config.STARTERS]
