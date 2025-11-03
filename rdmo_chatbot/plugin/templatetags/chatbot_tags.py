from django import template
from django.conf import settings
from django.utils.translation import get_language

from ..utils import get_chatbot_token

register = template.Library()

CHATBOT_LANGUAGES = {
    "en": "en-US",
    "de": "de-DE"
}


@register.simple_tag()
def chatbot_token(user):
    return get_chatbot_token(user)


@register.simple_tag()
def chatbot_language():
    current_language = get_language()
    return settings.CHATBOT_LANGUAGES[current_language]
