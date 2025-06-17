import logging
import os
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('-w', dest='watch', action='store_true', default=False)

    def handle(self, *args, **options):
        # find the path of the rdmo_chatbot directory
        chatbot_path = Path(__file__).parent.parent.parent
        chatbot_port = settings.CHAINLIT_URL.rsplit(':')[-1]

        chatbot_args = ['chainlit', 'run', 'app.py', '--port', chatbot_port]

        if options.get('watch'):
            chatbot_args.append('-w')

        subprocess.check_call(
            chatbot_args,
            cwd=chatbot_path,
            env={
                'PATH': os.getenv('PATH'),
                'PYTHONPATH': Path.cwd()
            }
        )
