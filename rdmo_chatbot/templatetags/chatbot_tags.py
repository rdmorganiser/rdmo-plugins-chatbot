import base64
import json

from django import template

from ..utils import get_chainlit_project, get_chainlit_token

register = template.Library()


@register.simple_tag()
def chainlit_token(user):
    return get_chainlit_token(user)


@register.simple_tag()
def chainlit_project(project):
    return base64.b64encode(json.dumps(get_chainlit_project(project)).encode()).decode()
