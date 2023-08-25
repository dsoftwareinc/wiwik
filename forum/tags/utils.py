from collections import Counter
from typing import List

from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from forum.models import Question, TagFollow, VoteActivity
from tags.apps import logger
from tags.models import Tag


def day_beginning(dt=None) -> timezone.datetime:
    if not dt:
        dt = timezone.now()
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def users_with_most_reputation_since(
        tag: Tag, count: int = 3, since: timezone.datetime = None,
        exclude_usernames: List[str] = None) -> List[str]:
    """Get users with most votes on tag since date
    :param tag: tag to check
    :param count: max number of usernames to return
    :param since: reputation since what date?
    """
    if since is None:
        since = timezone.datetime.min
    if exclude_usernames is None:
        exclude_usernames = []
    res = (VoteActivity.objects
           .filter(question__tags=tag, created_at__gte=since, target__is_active=True)
           .exclude(target__username__in=exclude_usernames)
           .values('target', 'question__tags')
           .annotate(tot=Sum('reputation_change'))
           .order_by('-tot')
           .values_list('target__username', flat=True))[:count]
    return res


def update_tag_stats_for_tag(tag: Tag):
    tag.number_of_questions = (Question.objects
                               .filter(tags__tag_word__iexact=tag.tag_word)
                               .count())

    seven_days_ago = (timezone.now() - timezone.timedelta(days=7))
    tag.number_asked_this_week = (Question.objects.
                                  filter(tags__tag_word__iexact=tag.tag_word,
                                         created_at__gte=seven_days_ago)
                                  .count())
    begining_of_day = day_beginning()
    tag.number_asked_today = (Question.objects
                              .filter(tags__tag_word__iexact=tag.tag_word,
                                      created_at__gte=begining_of_day)
                              .count())

    tag.number_followers = (TagFollow.objects.filter(tag=tag).count())

    experts_usernames = users_with_most_reputation_since(tag, count=settings.NUMBER_OF_TAG_EXPERTS)
    tag.experts = ','.join(experts_usernames) if len(experts_usernames) > 0 else None

    stars_usernames = users_with_most_reputation_since(
        tag,
        since=timezone.now() - timezone.timedelta(days=30),
        exclude_usernames=experts_usernames,
        count=settings.NUMBER_OF_TAG_RISING_STARS)
    tag.stars = ','.join(stars_usernames) if len(stars_usernames) > 0 else None
    tag.updated_at = timezone.now()

    # Calculate related tags
    tag_questions = Question.objects.filter(tags__tag_word__iexact=tag.tag_word)
    tags = [t.tag_word for q in tag_questions for t in q.tags.all()]
    tags_counter = Counter(tags)
    del tags_counter[tag.tag_word]
    tag.related = ','.join([i[0] for i in tags_counter.most_common(3)])

    tag.save()
    logger.info(f"Updated {tag}")
