import os
import shutil
import tempfile

from django.core.management.base import CommandParser

from wiwik_lib.utils import ManagementCommand
from forum.models import Question
from forum.views import thread_markdown_bytesio


def question_markdown(q: Question) -> str:
    io = thread_markdown_bytesio(q)
    return io.getvalue().decode("utf8")


class Command(ManagementCommand):
    help = "Export all questions in the forum"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--filename", type=str, required=True, help="archive name")

    def handle(self, filename: str, *args, **options):
        dirpath = tempfile.mkdtemp()
        self.print(f"Exporting forum to directory {dirpath}")
        if not os.path.isdir(dirpath):
            self.print(f"Directory {dirpath} does not exist, exiting")
            exit(1)
        question_qs = Question.objects.all()
        for q in question_qs:
            markdown_file = open(os.path.join(dirpath, f"{q.id}.md"), "w")
            markdown_file.write(question_markdown(q))
            markdown_file.close()
        shutil.make_archive(filename, "zip", dirpath)
        self.print(f"Archive created, cleaning up {dirpath}")
        shutil.rmtree(dirpath)
