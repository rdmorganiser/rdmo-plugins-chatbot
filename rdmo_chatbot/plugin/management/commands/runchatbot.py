import importlib
import json
import logging
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string

from rdmo.core.utils import get_languages

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-w", "--watch", dest="watch", action="store_true", default=False)
        parser.add_argument("-d", "--debug", dest="debug", action="store_true", default=False)
        parser.add_argument("--host", dest="host", default="localhost")
        parser.add_argument("--port", dest="port", default="8080")
        parser.add_argument("--root-path", dest="root-path", default=None)

    def handle(self, *args, **options):
        # find the path of the rdmo_chatbot directory
        chatbot_module = importlib.import_module("rdmo_chatbot.chatbot")
        chatbot_path = chatbot_module.__path__[0]

        chatbot_args = ["chainlit", "run", "app.py", "--headless"] + [
            f"--{key}" if value is True else f"--{key}={value}"
            for key, value in options.items()
            if key in ["watch", "debug", "host", "port", "root-path"] and value
        ]

        chatbot_config = {
            name[8:]: getattr(settings, name)
            for name in dir(settings)
            if name.startswith("CHATBOT_")
        }

        # add templates to config
        for lang_code, _, _ in get_languages():
            for key in ["confirmation", "continuation"]:
                template_name = f"chatbot/chatbot_{key}_{lang_code}.txt"
                try:
                    rendered_template  = render_to_string(template_name)
                    chatbot_config[f"{key}_{lang_code}".upper()] = rendered_template
                except TemplateDoesNotExist:
                    pass

        chatbot_env = os.environ.copy()
        chatbot_env["PYTHONPATH"] = Path.cwd()
        chatbot_env["CHAINLIT_AUTH_SECRET"] = settings.CHATBOT_AUTH_SECRET
        chatbot_env["CHATBOT_CONFIG"] = json.dumps(chatbot_config)

        subprocess.check_call(
            chatbot_args,
            cwd=chatbot_path,
            env=chatbot_env
        )
