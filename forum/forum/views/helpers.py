import time
from typing import Optional

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db.models import QuerySet
from django.shortcuts import render

from wiwik_lib.utils import paginate_queryset
from forum import jobs
from forum.jobs.others import log_search
from forum.models import Question
from forum.views import utils, search
from wiwik_lib.models import user_model_defer_fields

AVAILABLE_ORDER_BY = ('mostviewed', 'unanswered', 'latest', 'unresolved',)


def _get_request_tab(request):
    res = utils.get_request_param(request, 'tab', 'latest')
    return res if res in AVAILABLE_ORDER_BY else 'latest'


def _get_request_query(request):
    return utils.get_request_param(request, 'q', None)


def _get_questions_queryset(
        base_queryset: QuerySet, tab: str, query: str, user: Optional[AbstractUser],
) -> QuerySet:
    base_queryset = base_queryset.select_related('author', ).defer(*user_model_defer_fields('author'))
    start_time = time.time()
    if query is not None:
        qs = search.query_method(base_queryset, query)
    elif tab == 'mostviewed':
        qs = base_queryset.all().order_by('-views')
    elif tab == 'unresolved':
        qs = (base_queryset
              .filter(type__in=Question.POST_TYPE_ACCEPTING_ANSWERS, has_accepted_answer=False)
              .order_by('-created_at'))
    elif tab == 'unanswered':
        qs = (base_queryset
              .filter(type__in=Question.POST_TYPE_ACCEPTING_ANSWERS, answers_count=0)
              .order_by('-created_at'))
    else:
        qs = base_queryset.all().order_by('-created_at')
    if query and user:
        mstaken = int((time.time() - start_time) * 1000)
        first_five = list(qs.values_list('id', flat=True)[:5])
        jobs.start_job(log_search, user, query, first_five, mstaken)
    return qs


def render_questions(request, base_qs: QuerySet, header: str, extra: dict = None):
    tab = _get_request_tab(request)
    q = _get_request_query(request)
    all_questions_qs = _get_questions_queryset(
        base_qs.filter(space__isnull=True), tab, q, request.user)
    all_questions_qs = all_questions_qs.prefetch_related('tags', )
    page_number = request.GET.get('page', 1)
    page_qs = paginate_queryset(all_questions_qs, page_number, settings.QUESTIONS_PER_PAGE)
    context = {
        'all_questions': page_qs,
        'tab': tab if q is None else None,
        'header': header,
        'tag_watched': None,
    }
    if q:
        context['query'] = q
    if extra is not None:
        context = context | extra
    return render(request, 'main/questions.html', context)
