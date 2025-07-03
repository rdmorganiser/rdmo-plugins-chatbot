import base64
import json
import os
from http.cookies import SimpleCookie

import chainlit as cl
import jwt


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
