from tags.models import Tag
from wiwik_lib.utils import ManagementCommand


class Command(ManagementCommand):
    """This command should be run once."""
    help = 'Fix tag author to be the author of the first question with the tag'

    def handle(self, *args, **options):
        tag_qs = Tag.objects.all()
        count = 0
        for tag in tag_qs:
            if tag.author is not None:
                self.print(f"Tag {tag.tag_word} already has author set to {tag.author.username}, skipping")
                continue
            first_question = tag.question_set.all().order_by('created_at').first()
            if first_question is None:
                self.print(f"Tag {tag.tag_word} does not have questions...")
                continue
            tag.author = first_question.author
            tag.save()
            count += 1
        self.print(f"{count} tags have been updated")
