import time
from typing import Optional

from constance import config
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.shortcuts import render

from common import utils
from common.utils import TabEnum
from forum import jobs
from forum.jobs.others import log_search
from forum.models import Question
from forum.views import search
from spaces.models import Space
from userauth.models import ForumUser
from wiwik_lib.models import user_model_defer_fields
from wiwik_lib.utils import paginate_queryset


def get_questions_queryset(
    base_queryset: QuerySet,
    tab: Optional[str],
    query: Optional[str],
    user: Optional[AbstractUser],
) -> QuerySet:
    base_queryset = base_queryset.select_related(
        "author",
    ).defer(*user_model_defer_fields("author"), "source", "source_id", "link")
    start_time = time.time()
    if query is not None:
        qs = search.query_method(base_queryset, query)
    elif tab == TabEnum.MOST_VIEWED.value:
        qs = base_queryset.all().order_by("-views")
    elif tab == TabEnum.UNRESOLVED.value:
        qs = base_queryset.filter(type__in=Question.POST_TYPE_ACCEPTING_ANSWERS, has_accepted_answer=False).order_by(
            "-created_at"
        )
    elif tab == TabEnum.UNANSWERED.value:
        qs = base_queryset.filter(type__in=Question.POST_TYPE_ACCEPTING_ANSWERS, answers_count=0).order_by(
            "-created_at"
        )
    else:
        qs = base_queryset.all().order_by("-type", "-created_at")
    if query and user:
        mstaken = int((time.time() - start_time) * 1000)
        first_five = list(qs.values_list("id", flat=True)[:5])
        jobs.start_job(log_search, user, query, first_five, mstaken)
    return qs


def get_restricted_space_ids(user: ForumUser) -> list[int]:
    return list(Space.objects.filter(restricted=True).values_list("id", flat=True))


def render_questions(request, base_qs: QuerySet, header: str, extra: dict = None):
    tab = utils.get_request_tab(request)
    q = utils.get_request_param(request, "q", None)
    restricted_spaces = get_restricted_space_ids(request.user)
    all_questions_qs = get_questions_queryset(base_qs.exclude(space_id__in=restricted_spaces), tab, q, request.user)
    all_questions_qs = all_questions_qs.prefetch_related(
        "tags",
    )
    page_number = int(utils.get_request_param(request, "page", "1"))
    page_qs = paginate_queryset(all_questions_qs, page_number, config.QUESTIONS_PER_PAGE)
    context = {
        "all_questions": page_qs,
        "tab": tab if q is None else None,
        "header": header,
        "tag_watched": None,
    }
    if q:
        context["query"] = q
    if extra is not None:
        context = context | extra
    return render(request, "main/questions.html", context)
