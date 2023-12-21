from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import F, Count
from django.shortcuts import render, redirect

from forum.models import QuestionBookmark, VoteActivity, UserTagStats, Question, Answer
from userauth.models import ForumUser, UserVisit
from userauth.views.common import get_request_param
from wiwik_lib.models import Follow
from wiwik_lib.utils import paginate_queryset

ITEMS_PER_PAGE = 20
TABS = (
    "questions",
    "answers",
    "votes",
    "reputation",
    "following",
    "bookmarks",
    "badges",
)


def get_user_forum_data(seeuser: ForumUser, tab: str, page_number: int):
    items = []
    question_content_type = ContentType.objects.get(app_label="forum", model="question")
    counters = {
        "questions": Question.objects.filter(author=seeuser).count(),
        "answers": Answer.objects.filter(author=seeuser).count(),
        "votes": VoteActivity.objects.filter(source=seeuser).count(),
        "following": Follow.objects.filter(
            user=seeuser, content_type=question_content_type
        ).count(),
        "reputation": (
            VoteActivity.objects.filter(
                target=seeuser, reputation_change__isnull=False
            ).count()
        ),
        "bookmarks": QuestionBookmark.objects.filter(user=seeuser).count(),
        "badges": (
            VoteActivity.objects.filter(target=seeuser, badge__isnull=False).count()
        ),
    }

    if tab == "questions":
        items = Question.objects.filter(author=seeuser, is_anonymous=False).order_by(
            "-created_at"
        )
    if tab == "answers":
        items = Answer.objects.filter(author=seeuser).order_by("-created_at")
    if tab == "votes":
        items = (
            VoteActivity.objects.filter(source=seeuser)
            .annotate(year=F("created_at__year"))
            .order_by("-created_at")
        )
    if tab == "reputation":
        items = VoteActivity.objects.filter(target=seeuser).order_by("-created_at")
    if tab == "badges":
        items = (
            VoteActivity.objects.filter(target=seeuser, badge__isnull=False)
            .values(
                pk=F("badge__id"),
                name=F("badge__name"),
                type=F("badge__type"),
                description=F("badge__description"),
            )
            .annotate(count=Count("name"))
            .order_by("name")
        )
    if tab == "following":
        items = [
            follow.content_object
            for follow in Follow.objects.filter(
                user=seeuser, content_type=question_content_type
            ).order_by("-created_at")
        ]
    if tab == "bookmarks":
        items = QuestionBookmark.objects.filter(user=seeuser).order_by("-created_at")
    items = paginate_queryset(items, page_number, ITEMS_PER_PAGE)
    return items, counters


@login_required
def view_profile(request, username: str, tab: str):
    seeuser = ForumUser.objects.filter(username=username).first()
    if tab not in TABS:
        tab = "questions"
    if seeuser is None:
        messages.error(request, f"Couldn't find user {username}", "danger")
        return redirect("forum:list")
    is_self_profile = seeuser == request.user
    last_visit = UserVisit.objects.filter(user=seeuser).order_by("-visit_date").first()
    date_joined = seeuser.date_joined
    page_number = get_request_param(request, "page", 1)
    items, counters = get_user_forum_data(seeuser, tab, page_number)
    last_badge = (
        VoteActivity.objects.filter(badge__isnull=False).order_by("created_at").first()
    )
    context = {
        "items": items,
        "last_visit": last_visit,
        "seeuser": seeuser,
        "date_joined": date_joined,
        "tab": tab,
        "is_self_profile": is_self_profile,
        "counters": counters,
        "title": f"wiwik - User {seeuser.display_name()}",
        "last_badge": last_badge,
        "user_top_tags": (
            UserTagStats.objects.filter(user=seeuser, reputation__gt=0)
            .order_by("-reputation")
            .prefetch_related("tag")[:3]
        ),
    }

    if tab == "following":
        context["user_tag_stats"] = (
            UserTagStats.objects.filter(user=seeuser)
            .order_by("-reputation")
            .prefetch_related("tag")
        )
    return render(request, "userauth/profile.html", context)
