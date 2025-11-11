import chainlit as cl
from utils import get_adapter, get_config, get_user

config = get_config()
adapter = get_adapter(config)


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
        await adapter.on_user_message(message)


@cl.on_window_message
async def on_window_message(message):
    await adapter.on_system_message(message)


@cl.action_callback("on_transfer")
async def on_transfer(action):
    await adapter.on_transfer(action)


@cl.action_callback("on_contact")
async def on_contact(action):
    await adapter.on_contact(action)


@cl.on_logout
async def on_logout(request, response):
    response.delete_cookie("chatbot_token")
