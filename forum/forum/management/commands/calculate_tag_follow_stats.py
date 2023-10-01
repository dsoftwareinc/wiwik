from wiwik_lib.utils import ManagementCommand
from forum.jobs import recalculate_user_tag_stats
from forum.models import UserTagStats


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
        user_tag_stats_list = UserTagStats.objects.all()
        for user_tag_stats in user_tag_stats_list:
            recalculate_user_tag_stats(user_tag_stats)
