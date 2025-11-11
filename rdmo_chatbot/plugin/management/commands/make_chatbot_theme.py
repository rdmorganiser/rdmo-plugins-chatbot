import importlib
from pathlib import Path
from shutil import copyfile, copytree

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--path", default=Path("theme"), type=Path, help="Path to the new theme [default: theme]")

    def setup(self, options):
        self.theme_path = options["path"]

        # find the path of the rdmo_chatbot directory
        chatbot_module = importlib.import_module("rdmo_chatbot.chatbot")
        self.chatbot_path = Path(chatbot_module.__path__[0])

    def copy(self, path):
        source_path = self.chatbot_path / path
        target_path = self.theme_path / path

        if target_path.exists():
            print(f"Skip {source_path} -> {target_path}. Target file exists.")
        else:
            print(f"Copy {source_path} -> {target_path}.")

            target_path.parent.mkdir(parents=True, exist_ok=True)

            if source_path.is_dir():
                copytree(source_path, target_path)
            else:
                copyfile(source_path, target_path)

    def handle(self, *args, **options):
        self.setup(options)

        self.theme_path.mkdir(exist_ok=True)

        self.copy(".chainlit")
        self.copy("chainlit.md")
        self.copy("chainlit_en-US.md")
        self.copy("chainlit_de-DE.md")
        self.copy("public")

        print("Done")
