import logging
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

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
        chatbot_path = Path(__file__).parent.parent.parent / "chatbot"

        chatbot_args = ["chainlit", "run", "app.py", "--headless"] + [
            f"--{key}" if value is True else f"--{key}={value}"
            for key, value in options.items()
            if key in ["watch", "debug", "host", "port", "root-path"] and value
        ]

        print(" ".join(chatbot_args))

        subprocess.check_call(
            chatbot_args,
            cwd=chatbot_path,
            env={
                "PATH": os.getenv("PATH"),
                "PYTHONPATH": Path.cwd(),
                "CHAINLIT_AUTH_SECRET": settings.CHAINLIT_AUTH_SECRET,
            },
        )
