from datetime import datetime, timedelta

from django import template
from django.conf import settings

import jwt

from rdmo.accounts.utils import get_full_name

register = template.Library()


def get_chatbot_token(user):
    token_data = {
        "identifier": user.username,
        "display_name": get_full_name(user),
        "metadata": {},
        "exp": datetime.utcnow() + timedelta(minutes=60 * 24),
    }

    return jwt.encode(token_data, settings.CHATBOT_AUTH_SECRET, algorithm="HS256")
