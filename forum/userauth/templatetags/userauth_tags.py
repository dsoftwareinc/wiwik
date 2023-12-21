from datetime import date
from typing import List, Dict

from django import template
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from userauth.models import ForumUser

register = template.Library()


@register.simple_tag()
def class_for_votes(votes: int):
    votes = 0 if votes == "" or votes is None else int(votes)
    if votes > 0:
        return "bg-success"
    elif votes < 0:
        return "bg-danger"
    else:
        return "bg-secondary"


def get_created_at(obj):
    if (
        obj.created_at.tzinfo is not None
        and obj.created_at.tzinfo.utcoffset(obj.created_at) is not None
    ):
        return obj.created_at
    return timezone.make_aware(obj.created_at, timezone.get_fixed_timezone(0))


@register.filter()
def sort_list_created_at(lst: List):
    return sorted(lst, key=get_created_at, reverse=True)


@register.filter()
def get_val(d: Dict, key: str):
    return d.get(key)


@register.filter()
def dayssince(d: date, add_suffix: bool = True):
    diff = (date.today() - d).days
    parts = []
    if diff == 0:
        return "today"
    if diff > 365:
        parts.append(f"{diff // 365} years")
        diff = diff % 365
    if diff > 30:
        parts.append(f"{diff // 30} months")
        diff = diff % 30
    if diff > 0:
        parts.append(f"{diff} days")
    res = ", ".join(parts) + (" ago" if add_suffix else "")
    return res


@register.filter()
def latest_bookmarks(u: ForumUser, count=settings.MAX_BOOKMARK_ITEMS):
    return u.bookmarks.all().select_related("question").order_by("-created_at")[:count]


@register.filter()
def latest_reputation(u: ForumUser, count=settings.MAX_REPUTATION_ITEMS):
    return (
        u.reputation_votes.all()
        .select_related("question")
        .order_by("-created_at")[:count]
    )


@register.filter
def unseen_reputation_sum(u: ForumUser):
    return (
        u.reputation_votes.filter(seen__isnull=True, reputation_change__isnull=False)
        .aggregate(Sum("reputation_change"))
        .get("reputation_change__sum", 0)
        or 0
    )
