from functools import partial

from forum import models
from userauth.models import ForumUser
from .utils import TRIGGER_EVENT_TYPES, BadgeType, BadgeData, BadgeCalculation


def user_answers_query(
    min_votes: int, required: int, user: ForumUser
) -> BadgeCalculation:
    count = models.Answer.objects.filter(author=user, votes__gte=min_votes).count()
    return count // required, count % required


def user_accepted_answers_with_no_votes(
    required: int, user: ForumUser
) -> BadgeCalculation:
    count = (
        models.Answer.objects.exclude(question__author=user)
        .filter(author=user, votes=0, is_accepted=True)
        .count()
    )
    return count // required, count % required


def user_answer_not_accepted_higher_score(user: ForumUser) -> BadgeCalculation:
    # answers not accepted for questions with accepted answer
    answer_qs = models.Answer.objects.filter(
        author=user, is_accepted=False, question__has_accepted_answer=True
    )
    count = 0
    for answer in answer_qs:
        # find accepted answer
        accepted_answer = answer.question.answer_set.filter(is_accepted=True).first()
        if accepted_answer is None:
            continue
        if answer.votes > accepted_answer.votes + 5:
            count += 1
    return count, 0


answer_badges = [
    BadgeData(
        "Teacher",
        "Answer a question with score of 1 or more",
        partial(user_answers_query, 1, 1),
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Upvote"],
        group=0,
        required=1,
    ),
    BadgeData(
        "Tenacious",
        "5 accepted answers with no votes",
        partial(user_accepted_answers_with_no_votes, 5),
        BadgeType.SILVER,
        True,
        TRIGGER_EVENT_TYPES["Accept answer"],
        group=1,
        required=5,
    ),
    BadgeData(
        "Unsung Hero",
        "10 accepted answers with no votes",
        partial(user_accepted_answers_with_no_votes, 10),
        BadgeType.GOLD,
        True,
        TRIGGER_EVENT_TYPES["Accept answer"],
        group=1,
        required=10,
    ),
    BadgeData(
        "Populist",
        "Highest scoring answer that outscored the accepted answer by more than 5",
        user_answer_not_accepted_higher_score,
        BadgeType.GOLD,
        True,
        TRIGGER_EVENT_TYPES["Upvote"],
        group=3,
    ),
]
