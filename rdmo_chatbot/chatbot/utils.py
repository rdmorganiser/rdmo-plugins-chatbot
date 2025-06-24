import json
from http.cookies import SimpleCookie

from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import RequestFactory

import chainlit as cl
from chainlit import make_async

from rdmo.accounts.utils import get_full_name
from rdmo.projects.views import ProjectExportView


def sync_get_user(headers):
    cookies = SimpleCookie()
    cookies.load(headers.get("cookie", ""))
    session_cookie = cookies.get("sessionid")
    if session_cookie:
        session_key = session_cookie.value
        try:
            session = Session.objects.get(session_key=session_key)
            session_data = session.get_decoded()

            user_id = session_data.get("_auth_user_id")
            if user_id:
                User = get_user_model()
                user = User.objects.get(pk=user_id)
                return cl.User(identifier=user.username, display_name=get_full_name(user))
        except Session.DoesNotExist:
            pass


def sync_get_project(user, project_id):
    request_factory = RequestFactory()
    request = request_factory.get("/")
    request.user = get_user_model().objects.get(username=user.identifier)
    response = ProjectExportView.as_view()(request, pk=project_id, format="json")
    return json.dumps(json.loads(response.content))


get_user = make_async(sync_get_user)
get_project = make_async(sync_get_project)
