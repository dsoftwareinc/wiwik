from importlib import import_module

from django.core.management.base import CommandParser

from wiwik_lib.utils import ManagementCommand


def is_job(func):
    return hasattr(func, "delay")


class Command(ManagementCommand):
    help = "Run a job"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("-m", "--module", type=str, default="forum.jobs", help="Module to load")
        parser.add_argument("job", nargs="?", type=str, help="Job to run")

    def list_jobs(self):
        from forum import jobs

        for k, member in jobs.__dict__.items():
            if callable(member) and hasattr(member, "delay"):
                self.print(member.__name__)

    def handle(self, module: str, job: str, *args, **options):
        if job is None:
            self.list_jobs()
            return
        self.print(f"Importing module {module}")
        module_to_load = import_module(module)
        func = getattr(module_to_load, job)
        func()
