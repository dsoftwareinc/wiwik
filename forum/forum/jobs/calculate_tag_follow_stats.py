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
def recalculate_tag_follow_stats(tagfollow: models.TagFollow):
    if tagfollow is None:
        logger.warning('Entered recalculate_tag_follow_stats with tagfollow=None')
        return
    tagfollow.questions_by_user = models.Question.objects.filter(author=tagfollow.user, tags=tagfollow.tag).count()
    tagfollow.answers_by_user = (models.Answer.objects
                                 .filter(author=tagfollow.user, question__tags=tagfollow.tag)
                                 .count())
    tagfollow.reputation = (models.VoteActivity.objects
                            .filter(target=tagfollow.user, question__tags=tagfollow.tag)
                            .aggregate(rep=Sum('reputation_change'))
                            .get('rep') or 0
                            )
    last_month = timezone.now() - timedelta(days=30)
    tagfollow.reputation_last_month = (models.VoteActivity.objects
                                       .filter(target=tagfollow.user,
                                               question__tags=tagfollow.tag,
                                               created_at__gte=last_month, )
                                       .aggregate(rep=Sum('reputation_change'))
                                       .get('rep') or 0
                                       )
    tagfollow.save()
    update_tag_stats_for_tag(tagfollow.tag)
    logger.debug(f'Recalculated tag follow stats, now: {tagfollow}')


@job
def update_tag_follow_stats(post_id: int, user_id: int):
    post = Question.objects.get(id=post_id)
    user = ForumUser.objects.get(id=user_id)
    tags_to_update = post.tags.all()
    for tag in tags_to_update:
        tag_follow = models.TagFollow.objects.filter(tag=tag, user=user).first()
        recalculate_tag_follow_stats(tag_follow)
