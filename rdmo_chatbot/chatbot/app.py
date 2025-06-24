import os

import django

import chainlit as cl
from openai import AsyncOpenAI

# set the location of the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from django.conf import settings  # noqa: E402

from utils import get_project, get_user  # noqa: E402

client = AsyncOpenAI(
    base_url=settings.CHAINLIT_OPENAI_URL,
    api_key=settings.CHAINLIT_OPENAI_API_KEY,
)

cl.instrument_openai()


@cl.header_auth_callback
async def header_auth_callback(headers):
    return await get_user(headers)


@cl.on_chat_start
async def on_chat_start(*args, **kwargs):
    system_prompt = (
        "You are a helpful bot, you use your deep knowledge of research data management "
        "to help the user to describe their research project and the data management therein. "
    )

    user = cl.user_session.get("user")
    system_prompt += f"The name of the user is {user.display_name}. "

    context = await cl.CopilotFunction(name="getContext", args={}).acall()
    if "project_id" in context:
        project = await get_project(user, context["project_id"])
        system_prompt += f"The user already entered the following information about their research project: {project}"

    cl.user_session.set("system_prompt", system_prompt)


@cl.on_message
async def on_message(message: cl.Message):
    messages = [
        {"content": cl.user_session.get("system_prompt"), "role": "system"},
        *cl.chat_context.to_openai(),
    ]

    response = await client.chat.completions.create(messages=messages, **settings.CHAINLIT_SETTINGS)

    await cl.Message(content=response.choices[0].message.content).send()


@cl.set_starters
async def set_starters():
    return [cl.Starter(**starter) for starter in settings.CHATBOT_STARTERS]
