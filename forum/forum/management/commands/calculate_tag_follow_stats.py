from wiwik_lib.utils import ManagementCommand
from forum.jobs import recalculate_tag_follow_stats
from forum.models import TagFollow


class Command(ManagementCommand):
    help = 'Calculate tag follows statistics and tags-statistics'

    def handle(self, *args, **options):
        # Version 1:
        # TagFollow.objects.all().update(questions_by_user=0, answers_by_user=0)
        # question_qs = Question.objects.all()
        # for question in question_qs:
        #     update_tag_follow_stats(question)
        # answer_qs = Answer.objects.all()
        # for answer in answer_qs:
        #     update_tag_follow_stats(answer)
        tag_follow_qs = TagFollow.objects.all()
        for tag_follow in tag_follow_qs:
            recalculate_tag_follow_stats(tag_follow)
