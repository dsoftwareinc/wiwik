from functools import partial

from django.db.models import Count, F

from forum.models import QuestionComment
from userauth.models import ForumUser, UserVisit
from .utils import (
    user_authored_vs_required,
    BadgeData,
    TRIGGER_EVENT_TYPES,
    BadgeType,
    BadgeCalculation,
)

user_commented_10 = partial(user_authored_vs_required, QuestionComment, 10)


def user_edited_profile(user: ForumUser) -> BadgeCalculation:
    return (1, 0) if (user.about_me and user.title) else (0, 0)


def user_commented_10_with_5_upvotes(user: ForumUser) -> BadgeCalculation:
    count = QuestionComment.objects.filter(author=user, votes__gte=5).count()
    return count // 10, count % 10


def user_visited_30_consecutive_days(user: ForumUser) -> BadgeCalculation:
    visited_30_or_more = UserVisit.objects.filter(user=user, consecutive_days__gte=30).exists()
    count = 1 if visited_30_or_more else 0
    closest = (
        UserVisit.objects.filter(user=user)
        .annotate(closest=F("consecutive_days") % 30)
        .order_by("-closest")
        .values_list("closest", flat=True)
        .first()
        or 0
    )
    return count, closest


def user_login_from_multiple_cities(user: ForumUser) -> BadgeCalculation:
    count = (
        UserVisit.objects.filter(user=user)
        .values("country")
        .annotate(cities=Count("city", distinct=True))
        .filter(cities__gt=1)
        .count()
    )
    return count, 0


def user_login_from_multiple_countries(required: int, user: ForumUser) -> BadgeCalculation:
    countries = UserVisit.objects.filter(user=user).values("country").distinct().count()
    return countries // required, countries % required


participation_badges = [
    BadgeData(
        "Autobiographer",
        "Edit the title and about me section in profile",
        user_edited_profile,
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Edit profile"],
        group=1,
    ),
    BadgeData(
        "Commenter",
        "Wrote 10 comments",
        user_commented_10,
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Create comment"],
        group=2,
        required=10,
    ),
    BadgeData(
        "Pundit",
        "Wrote 10 comments that have 5 upvotes",
        user_commented_10_with_5_upvotes,
        BadgeType.BRONZE,
        False,
        TRIGGER_EVENT_TYPES["Upvote"],
        group=3,
    ),
    BadgeData(
        "Workaholic",
        "Visit the site each day for 30 consecutive days. (Days are counted in UTC.)",
        user_visited_30_consecutive_days,
        BadgeType.GOLD,
        True,
        TRIGGER_EVENT_TYPES["Visit"],
        group=4,
        required=30,
    ),
    BadgeData(
        "Commuter",
        "Visit the site from multiple cities (in the same country)",
        user_login_from_multiple_cities,
        BadgeType.BRONZE,
        True,
        TRIGGER_EVENT_TYPES["Visit"],
        group=5,
    ),
    BadgeData(
        "Traveller",
        "Visit the site from more than 1 country",
        partial(user_login_from_multiple_countries, 2),
        BadgeType.SILVER,
        True,
        TRIGGER_EVENT_TYPES["Visit"],
        group=6,
        required=2,
    ),
    BadgeData(
        "Digital Nomad",
        "Visit the site from 5 countries or more",
        partial(user_login_from_multiple_countries, 5),
        BadgeType.GOLD,
        True,
        TRIGGER_EVENT_TYPES["Visit"],
        group=6,
        required=5,
    ),
]
