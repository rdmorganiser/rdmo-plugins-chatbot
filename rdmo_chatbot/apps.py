from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class ChatbotConfig(AppConfig):
    name = "rdmo_chatbot"

    def ready(self):
        middleware_list = settings.MIDDLEWARE
        if "rdmo_chatbot.middleware.ChatbotMiddleware" not in middleware_list:
            raise ImproperlyConfigured("rdmo_chatbot.middleware.ChatbotMiddleware must be added to settings.MIDDLEWARE")
