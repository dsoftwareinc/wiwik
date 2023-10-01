from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone
from scheduler import job

from forum import models
from forum.jobs.base import logger
from forum.models import Question
from tags.utils import update_tag_stats_for_tag
from userauth.models import ForumUser


@job
def recalculate_user_tag_stats(user_tag_stats: models.UserTagStats):
    if user_tag_stats is None:
        logger.warning('Entered recalculate_tag_follow_stats with user_tag_stats=None')
        return
    user_tag_stats.questions_by_user = models.Question.objects.filter(author=user_tag_stats.user, tags=user_tag_stats.tag).count()
    user_tag_stats.answers_by_user = (models.Answer.objects
                                      .filter(author=user_tag_stats.user, question__tags=user_tag_stats.tag)
                                      .count())
    user_tag_stats.reputation = (models.VoteActivity.objects
                                 .filter(target=user_tag_stats.user, question__tags=user_tag_stats.tag)
                                 .aggregate(rep=Sum('reputation_change'))
                                 .get('rep') or 0
                                 )
    last_month = timezone.now() - timedelta(days=30)
    user_tag_stats.reputation_last_month = (models.VoteActivity.objects
                                            .filter(target=user_tag_stats.user,
                                                    question__tags=user_tag_stats.tag,
                                                    created_at__gte=last_month, )
                                            .aggregate(rep=Sum('reputation_change'))
                                            .get('rep') or 0
                                            )
    user_tag_stats.save()
    update_tag_stats_for_tag(user_tag_stats.tag)
    logger.debug(f'Recalculated tag follow stats, now: {user_tag_stats}')


@job
def update_tag_follow_stats(post_id: int, user_id: int):
    post = Question.objects.get(id=post_id)
    user = ForumUser.objects.get(id=user_id)
    tags_to_update = post.tags.all()
    for tag in tags_to_update:
        tag_follow = models.UserTagStats.objects.filter(tag=tag, user=user).first()
        recalculate_user_tag_stats(tag_follow)
