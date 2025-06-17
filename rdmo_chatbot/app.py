import os

import django

import chainlit as cl
from chainlit import make_async
from openai import AsyncOpenAI

# set the location of the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django.setup()

from django.conf import settings  # noqa: E402
from django.contrib.auth.models import User  # noqa: E402
from django.test import RequestFactory  # noqa: E402

from rdmo.projects.views import ProjectExportView  # noqa: E402

client = AsyncOpenAI(
    base_url=settings.CHAINLIT_OPENAI_URL,
    api_key=settings.CHAINLIT_OPENAI_API_KEY,
)

cl.instrument_openai()


@cl.on_chat_start
async def on_chat_start():
    project_export_response = await async_get_project_export(1)
    cl.user_session.set("system_prompt", (
        "You are a helpful bot, you use your deep knowledge of research "
        "data managment to info the user about RDMO on each question. The "
        "User already entered the following information their reserch project: "
        + project_export_response.content.decode()
    ))


@cl.on_message
async def on_message(message: cl.Message):
    messages = [
        {
            "content": cl.user_session.get('system_prompt'),
            "role": "system"
        },
        *cl.chat_context.to_openai(),
    ]

    response = await client.chat.completions.create(
        messages=messages,
        **settings.CHAINLIT_SETTINGS
    )

    await cl.Message(content=response.choices[0].message.content).send()


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(**starter) for starter in  settings.CHATBOT_STARTERS
    ]


def get_project_export(pk):
    request_factory = RequestFactory()
    request = request_factory.get('/')
    request.user = User.objects.get(pk=1)

    response = ProjectExportView.as_view()(request, pk=pk, format='json')
    return response


async_get_project_export = make_async(get_project_export)
