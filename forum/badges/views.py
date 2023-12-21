from django.contrib.auth.decorators import login_required
from django.db.models import Count, Value, When, Case, Q
from django.shortcuts import render, get_object_or_404

from badges.logic.utils import BadgeType
from badges.models import Badge
from wiwik_lib.utils import paginate_queryset
from forum.models import VoteActivity


@login_required
def view_single_badge(request, badge_id: int):
    badge = get_object_or_404(Badge, pk=badge_id)

    query_set = VoteActivity.objects.filter(
        badge=badge, target__is_active=True
    ).order_by("-created_at")
    page = request.GET.get("page", 1)
    items = paginate_queryset(query_set, page, 50)
    return render(
        request,
        "badges/badges.single.template.html",
        {
            "badge": badge,
            "items": items,
        },
    )


@login_required
def view_badges(request):
    items = list(
        Badge.objects.all()
        .annotate(
            users=Count("voteactivity", filter=Q(voteactivity__target__is_active=True))
        )
        .annotate(
            level=Case(
                When(type=BadgeType.BRONZE, then=Value(0)),
                When(type=BadgeType.SILVER, then=Value(1)),
                When(type=BadgeType.GOLD, then=Value(2)),
            )
        )
        .annotate(
            earned=Count("voteactivity", filter=Q(voteactivity__target=request.user))
        )
        .order_by("section", "group", "level")
    )
    recent_awards = VoteActivity.objects.filter(badge__isnull=False).order_by(
        "-created_at"
    )[:20]
    return render(
        request,
        "badges/badges.list.template.html",
        {
            "items": items,
            "recent": recent_awards,
        },
    )
