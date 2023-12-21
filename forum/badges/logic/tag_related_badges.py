from functools import partial

from django.db.models import Count

from badges.logic.utils import (
    user_authored_vs_required,
    BadgeData,
    TRIGGER_EVENT_TYPES,
    BadgeType,
    BadgeCalculation,
)
from tags.models import Synonym, TagEdit, Tag
from userauth.models import ForumUser


def tags_created_with_num_questions_vs_required(
    required: int, user: ForumUser
) -> BadgeCalculation:
    count = (
        Tag.objects.filter(author=user)
        .annotate(questions_count=Count("question"))
        .filter(questions_count__gte=required)
        .count()
    ) or 0
    closest = (
        Tag.objects.filter(author=user)
        .annotate(next=Count("question") % required)
        .order_by("-next")
        .values_list("next", flat=True)
        .first()
        or 0
    )
    return count, closest


tag_badges = [
    BadgeData(
        "Synonymizer",
        "Suggest a synonym that is accepted",
        partial(user_authored_vs_required, Synonym, 1),
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Synonym approved"],
        group=1,
    ),
    BadgeData(
        "Meticulous",
        "Suggest 10 accepted synonyms",
        partial(user_authored_vs_required, Synonym, 10),
        BadgeType.SILVER,
        True,
        TRIGGER_EVENT_TYPES["Synonym approved"],
        group=1,
        required=10,
    ),
    BadgeData(
        "Tag Editor",
        "First tag edit",
        partial(user_authored_vs_required, TagEdit, 1),
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Tag edit"],
        group=1,
    ),
    BadgeData(
        "Taxonomist",
        "Create a tag used by 20 questions",
        partial(tags_created_with_num_questions_vs_required, 20),
        BadgeType.SILVER,
        False,
        TRIGGER_EVENT_TYPES["Tag created"],
        group=2,
        required=20,
    ),
]
