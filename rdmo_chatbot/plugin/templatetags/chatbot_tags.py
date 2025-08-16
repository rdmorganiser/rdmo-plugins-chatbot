import base64
import json

from django import template

from ..utils import get_chatbot_project, get_chatbot_token

register = template.Library()


@register.simple_tag()
def chatbot_token(user):
    return get_chatbot_token(user)


@register.simple_tag()
def chatbot_project(project):
    return base64.b64encode(json.dumps(get_chatbot_project(project)).encode()).decode()
