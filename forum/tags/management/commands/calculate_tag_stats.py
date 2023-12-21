from wiwik_lib.utils import ManagementCommand
from tags.jobs import update_tag_stats


class Command(ManagementCommand):
    help = "Calculate tag follows statistics and tags-statistics"

    def handle(self, *args, **options):
        update_tag_stats()
