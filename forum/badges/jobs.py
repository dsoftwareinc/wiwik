from typing import Callable

from django.db.models import F, Count
from scheduler import job

from forum.models import VoteActivity
from userauth.models import ForumUser
from .apps import logger
from .logic.utils import BadgeType
from .models import Badge
from .populate_db import BADGE_LOGIC


def _check_badge_for_user(badge: Badge, user: ForumUser, method: Callable[[ForumUser], int]) -> bool:
    """
    Check whether user is entitled to a badge. If they do and the activity
    doesn't exist, create it

    Args:
        badge: Badge to check
        user: User to check
        method: Badge method logic.

    Returns:
        True if activity with the badge was created on this run for the user
    """
    if method is None:
        return False
    badge_count = VoteActivity.objects.filter(badge=badge, target=user).count()
    if badge.only_once and badge_count > 0:
        return False
    expected_count = method(user)[0]
    while expected_count < badge_count:  # User has more badges than expected
        logger.info(
            f'User has {badge_count} "{badge.name}" badges where they should have {expected_count} ' f"- removing last"
        )
        last = VoteActivity.objects.filter(badge=badge, target=user).order_by("-created_at").first()
        last.delete()
        badge_count = VoteActivity.objects.filter(badge=badge, target=user).count()
    if expected_count > badge_count:
        VoteActivity.objects.create(
            target=user,
            badge=badge,
        )
        if badge.type == BadgeType.GOLD:
            user.gold_badges += 1
        elif badge.type == BadgeType.SILVER:
            user.silver_badges += 1
        elif badge.type == BadgeType.BRONZE:
            user.bronze_badges += 1
        else:
            logger.error(f"No matching counter field for badge {badge.name} of type {badge.type}")
        user.save()
        return True
    return False


def check_users(badge: Badge) -> int:
    """
    Create badge activity for all users entitled.

    Args:
        badge: Badge to check.

    Returns:
        Number of users badge earning activity created for.
    """
    if badge is None:
        logger.warning("Got badge=None to check users for")
        return 0
    method = BADGE_LOGIC.get(badge.name, None)
    if method is None:
        logger.error(f"Couldn't find logic for badge '{badge.name}'")
        return 0
    res = 0
    user_qs = ForumUser.objects.all()
    for u in user_qs:
        if _check_badge_for_user(badge, u, method):
            res += 1
    logger.info(f"{res} users received {badge.name}")
    return res


def check_badge_for_all_users(badge_name: str):
    try:
        badge = Badge.objects.get(name=badge_name)
        check_users(badge)
    except Badge.DoesNotExist:
        logger.warning(f"Could not find badge {badge_name} in database, maybe the DB needs to be updated")
        return


def check_all_badges_for_user(user: ForumUser) -> int:
    """
    Go over all badges in BADGE_MAP and see which ones the user is entitled to.

    Args:
        user: User to check for

    Returns:
        Number of new badges created for user.

    """
    res = 0
    badge_qs = Badge.objects.all()
    for badge in badge_qs:
        method = BADGE_LOGIC.get(badge.name, None)
        if method is None:
            logger.error(f"Couldn't find logic for badge '{badge.name}'")
            continue
        res += _check_badge_for_user(badge, user, method)
    logger.info(f"User {user.username} earned {res} badges")
    return res


@job("cron")
def review_all_badges() -> None:
    """
    Iterate through badges in the system and create badge activities for
    all users entitled.

    Returns:
        None
    """
    badge_type_count = {}
    badge_qs = Badge.objects.all()
    for badge in badge_qs:
        logger.info(f"Checking users entitled to badge {badge.name}")
        badge_type_count[badge.type] = check_users(badge) + badge_type_count.get(badge.type, 0)
    for badge_type in badge_type_count:
        logger.info(f"{badge_type_count[badge_type]} users received {badge_type} badges")
    recalculate_user_badges_stats()


@job
def review_bagdes_event(event: int) -> None:
    badge_qs = Badge.objects.filter(trigger=event)
    for badge in badge_qs:
        logger.info(f"Checking users entitled to badge {badge.name}")
        check_users(badge)


@job
def recalculate_user_badges_stats():
    user_qs = ForumUser.objects.all()
    for user in user_qs:
        stats = user.additional_data
        badges_total_list = list(
            VoteActivity.objects.filter(target=user, badge__isnull=False)
            .values(type=F("badge__type"))
            .annotate(count=Count("type"))
            .values_list("type", "count")
        )
        badges_total_dict = {i[0]: i[1] for i in badges_total_list}
        stats.bronze_badges = badges_total_dict.get(BadgeType.BRONZE, 0)
        stats.silver_badges = badges_total_dict.get(BadgeType.SILVER, 0)
        stats.gold_badges = badges_total_dict.get(BadgeType.GOLD, 0)
        stats.save()
