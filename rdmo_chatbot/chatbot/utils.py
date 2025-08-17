import base64
import importlib
import json
import os
from http.cookies import SimpleCookie
from types import SimpleNamespace

import chainlit as cl
import jwt


def get_config():
    return SimpleNamespace(**json.loads(os.getenv("CHATBOT_CONFIG")))


def get_adapter(cl, config):
    adapter_module_name, adapter_class_name = config.ADAPTER.rsplit(".", 1)
    adapter_module = importlib.import_module(adapter_module_name)
    adapter_class = getattr(adapter_module, adapter_class_name)
    return adapter_class(cl, config)


def get_user(config, headers):
    cookies = SimpleCookie()
    cookies.load(headers.get("cookie", ""))

    cookie = cookies.get("chatbot_token")
    if not cookie:
        return None

    try:
        token = jwt.decode(cookie.value, config.AUTH_SECRET, algorithms=["HS256"])
        return cl.User(identifier=token["identifier"], metadata=token["metadata"], display_name=token["display_name"])
    except jwt.exceptions.InvalidSignatureError:
        return None


def parse_context(raw_context):
    return json.loads(base64.b64decode(raw_context).decode())
