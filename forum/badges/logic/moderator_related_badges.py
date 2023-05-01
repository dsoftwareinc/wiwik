from functools import partial

from forum import models
from forum.models import Question, Answer
from userauth.models import ForumUser
from .utils import BadgeData, TRIGGER_EVENT_TYPES, BadgeType, BadgeCalculation


def user_edited_count_vs_expected(required: int, user: ForumUser) -> BadgeCalculation:
    questions_edited = Question.objects.filter(editor=user).count()
    answers_edited = Answer.objects.filter(editor=user).count()
    total = questions_edited + answers_edited
    return divmod(total, required)


def user_upvoted_count_vs_expected(required: int, user: ForumUser) -> BadgeCalculation:
    upvoted_count = models.VoteActivity.objects.filter(source=user, reputation_change__gt=0).count()
    return divmod(upvoted_count, required)


def user_upvoted_competing_answers_count_vs_expected(
        required: int, user: ForumUser) -> BadgeCalculation:
    upvoted_count = models.VoteActivity.objects.filter(
        source=user, reputation_change__gt=0,
        question__answer__author=user,
        question__answer__votes__gt=0,
    ).count()
    return divmod(upvoted_count, required)


moderation_badges = [
    BadgeData('Editor', 'First edit',
              partial(user_edited_count_vs_expected, 1), BadgeType.BRONZE, True,
              TRIGGER_EVENT_TYPES['Update post'], group=1, required=1,
              ),
    BadgeData('Strunk & White', 'Edit 20 posts',
              partial(user_edited_count_vs_expected, 20), BadgeType.BRONZE, True,
              TRIGGER_EVENT_TYPES['Update post'], group=1, required=20,
              ),
    BadgeData('Copy editor', 'Edit 100 posts',
              partial(user_edited_count_vs_expected, 100), BadgeType.GOLD, False,
              TRIGGER_EVENT_TYPES['Update post'], group=1, required=100,
              ),
    BadgeData('Supporter', 'First upvote',
              partial(user_upvoted_count_vs_expected, 1), BadgeType.BRONZE, True,
              TRIGGER_EVENT_TYPES['Upvote'], group=2, required=1,
              ),
    BadgeData('Sportsmanship',
              'Upvote 10 answers on questions where an answer of yours has a positive score',
              partial(user_upvoted_competing_answers_count_vs_expected, 10), BadgeType.SILVER, True,
              TRIGGER_EVENT_TYPES['Upvote'], group=3, required=10,
              ),
]
