import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F, QuerySet
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils import timezone

from userauth.models import ForumUser
from userauth.views.common import get_request_param
from wiwik_lib.utils import paginate_queryset


def _calculate_start_date(tab: str, from_date: str) -> timezone.datetime:
    if from_date is not None:
        res = datetime.datetime.strptime(from_date, "%Y-%m-%d")
        if settings.USE_TZ:
            res = timezone.make_aware(res)
        return res
    today = timezone.now()
    map_days = {
        "month": 30,
        "week": 7,
        "quarter": 90,
        "year": 365,
    }
    days = map_days.get(tab, 30)
    return today - timezone.timedelta(days=days)


def _users_found_title(tab: str, queryset: QuerySet) -> str:
    total = ForumUser.objects.filter(is_superuser=False, is_active=True).count()
    if tab == "all":
        return f"{total} active users"
    count = queryset.count()
    return f"{count} out of {total} users in the last {tab}"


def render_request(request):
    query_username = get_request_param(request, "q", None)
    basic_query_set = ForumUser.objects.filter(is_superuser=False, is_active=True)
    tab = request.GET.get("tab", "all")
    if tab not in {"all", "month", "year", "week", "quarter"} or query_username is not None:
        tab = "all"
    from_date = request.GET.get("from_date", None)
    if query_username:
        basic_query_set = basic_query_set.filter(
            Q(username__icontains=query_username)
            | Q(name__icontains=query_username)
            | Q(email__icontains=query_username)
        )

    if tab == "all" and from_date is None:
        queryset = basic_query_set.annotate(reputation=F("additional_data__reputation_score"))
    else:
        start_date = _calculate_start_date(tab, from_date)
        queryset = basic_query_set.filter(
            reputation_votes__created_at__gte=start_date,
            reputation_votes__reputation_change__isnull=False,
        ).annotate(reputation=Sum("reputation_votes__reputation_change"))
    queryset = queryset.order_by("-reputation")

    page = request.GET.get("page", 1)
    users_page = paginate_queryset(queryset, page, 30)
    return loader.render_to_string(
        "userauth/users_list_data.html",
        {
            "users": users_page,
            "tab": tab,
            "from_date": from_date,
            "query": query_username,
            "count": queryset.count(),
            "title": _users_found_title(tab, queryset),
        },
    )


@login_required
def view_users_query(request):
    return HttpResponse(render_request(request))


@login_required
def view_users(request):
    tab = request.GET.get("tab", "all")
    content = render_request(request)

    return render(
        request,
        "userauth/users-list.html",
        {
            "content": content,
            "tab": tab,
            "title": "wiwik - Users",
        },
    )
