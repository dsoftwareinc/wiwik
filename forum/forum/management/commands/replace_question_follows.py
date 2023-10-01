from django.contrib.contenttypes.models import ContentType

from forum.models import QuestionFollow, UserTagStats
from wiwik_lib.models import Follow
from wiwik_lib.utils import ManagementCommand


class Command(ManagementCommand):
    help = 'Create Follow instead of QuestionFollow and UserTagStats.'

    def handle(self, *args, **options):
        questionfollow_qs = QuestionFollow.objects.all()
        for item in questionfollow_qs:
            content_type = ContentType.objects.get_for_model(item.question)
            f, created = Follow.objects.get_or_create(user=item.user, content_type=content_type,
                                                      object_id=item.question_id)
            if created:
                self.print(f'Created {f}')
        tagfollow_qs = UserTagStats.objects.all()
        for item in tagfollow_qs:
            content_type = ContentType.objects.get_for_model(item.tag)
            f, created = Follow.objects.get_or_create(user=item.user, content_type=content_type,
                                                      object_id=item.tag_id)
            if created:
                self.print(f'Created {f}')