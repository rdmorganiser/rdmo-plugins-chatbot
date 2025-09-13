from django import template

from ..utils import get_chatbot_token

register = template.Library()


@register.simple_tag()
def chatbot_token(user):
    return get_chatbot_token(user)
