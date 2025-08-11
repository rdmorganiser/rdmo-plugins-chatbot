from datetime import datetime, timedelta

from django import template
from django.conf import settings

import jwt

from rdmo.accounts.utils import get_full_name
from rdmo.projects.exports import AnswersExportMixin

register = template.Library()


def get_chainlit_token(user):
    token_data = {
        "identifier": user.username,
        "display_name": get_full_name(user),
        "metadata": {},
        "exp": datetime.utcnow() + timedelta(minutes=60 * 24),
    }

    return jwt.encode(token_data, settings.CHAINLIT_AUTH_SECRET, algorithm="HS256")


def get_chainlit_project(project):
    export_plugin = AnswersExportMixin()
    export_plugin.project = project
    export_plugin.snapshot = None

    data = export_plugin.get_data()
    return data
