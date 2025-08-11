import base64
import importlib
import json
import os
from http.cookies import SimpleCookie

import chainlit as cl
import jwt


def get_adapter(cl, settings):
    adapter_module_name, adapter_class_name = settings.CHAINLIT_ADAPTER.rsplit(".", 1)
    adapter_module = importlib.import_module(adapter_module_name)
    adapter_class = getattr(adapter_module, adapter_class_name)
    return adapter_class(cl, settings)


def get_user(headers):
    cookies = SimpleCookie()
    cookies.load(headers.get("cookie", ""))

    cookie = cookies.get("chainlit_token")
    if not cookie:
        return None

    try:
        token = jwt.decode(cookie.value, os.getenv("CHAINLIT_AUTH_SECRET"), algorithms=["HS256"])
        return cl.User(identifier=token["identifier"], metadata=token["metadata"], display_name=token["display_name"])
    except jwt.exceptions.InvalidSignatureError:
        return None


def get_project(project_data):
    return json.loads(base64.b64decode(project_data).decode())
