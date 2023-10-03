from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db.models import Sum
from django.utils import timezone

from forum import models
from tags.models import Tag
from tags.utils import update_tag_stats_for_tag
from wiwik_lib.views.follow_views import create_follow, delete_follow


def handle_user_tag_stats(tag: Tag, user: AbstractUser) -> None:
    questions_by_user = (models.Question.objects
                         .filter(author=user, tags=tag)
                         .count())
    answers_by_user = (models.Answer.objects
                       .filter(author=user, question__tags=tag)
                       .count())
    reputation = (models.VoteActivity.objects
                  .filter(target=user, question__tags=tag)
                  .aggregate(rep=Sum('reputation_change'))
                  .get('rep') or 0
                  )
    last_month = timezone.now() - timedelta(days=30)
    reputation_last_month = (models.VoteActivity.objects
                             .filter(target=user,
                                     question__tags=tag,
                                     created_at__gte=last_month, )
                             .aggregate(rep=Sum('reputation_change'))
                             .get('rep') or 0
                             )

    # Only if any number is bigger than 0, then stats object should be created
    should_have_stats = any((questions_by_user, answers_by_user, reputation, reputation_last_month))

    if not should_have_stats:
        models.UserTagStats.objects.filter(tag=tag, user=user).delete()
        return

    stats, _ = models.UserTagStats.objects.get_or_create(tag=tag, user=user)
    stats.questions_by_user = questions_by_user
    stats.answers_by_user = answers_by_user
    stats.reputation = reputation
    stats.reputation_last_month = reputation_last_month
    stats.save()
    update_tag_stats_for_tag(stats.tag)


def create_follow_tag(tag: Tag, user: AbstractUser) -> None:
    handle_user_tag_stats(tag, user)
    create_follow(tag, user)


def delete_follow_tag(tag: Tag, user: AbstractUser):
    handle_user_tag_stats(tag, user)
    delete_follow(tag, user)
