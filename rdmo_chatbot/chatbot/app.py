import os

import chainlit as cl
from utils import get_adapter, get_project, get_user

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.conf import settings

adapter = get_adapter(cl, settings)


@cl.header_auth_callback
def header_auth_callback(headers):
    return get_user(headers)


@cl.on_chat_start
async def on_chat_start(*args, **kwargs):
    user = cl.user_session.get("user")

    system_prompt = (
        "You are a helpful bot, you use your deep knowledge of research data management "
        "to help the user to describe their research project and the data management therein. "
    )

    system_prompt += f"The name of the user is {user.display_name}. "

    if cl.context.session.client_type == "copilot":
        context = await cl.CopilotFunction(name="getContext", args={}).acall()
        project_data = context.get("project")
        if project_data:
            project = get_project(project_data)
            system_prompt += (
                f"The user already entered the following information about their research project: {project}"
            )

    cl.user_session.set("system_prompt", system_prompt)


@cl.on_message
async def on_message(message: cl.Message):
    await adapter.on_message(message)


@cl.set_starters
async def set_starters():
    return [cl.Starter(**starter) for starter in settings.CHATBOT_STARTERS]
