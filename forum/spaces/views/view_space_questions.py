from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from common import utils
from forum.models import Question
from forum.views.helpers import _get_questions_queryset
from spaces.models import Space, SpaceMember
from spaces.views.access import validate_space_access
from wiwik_lib.utils import paginate_queryset


@login_required
def view_space_questions(request, space_id: int):
    if request.method != 'GET':
        raise Http404()
    space = get_object_or_404(Space, id=space_id)
    validate_space_access(space, request.user)
    page_number = request.GET.get('page', 1)
    main_query = Question.objects.filter(space=space)
    properties = space.properties.all()
    page_qs = paginate_queryset(main_query, page_number, settings.QUESTIONS_PER_PAGE)
    context = {
        'questions_list': page_qs,
        'header': f'Questions for space {space.short_name}',
        'space': space,
        'properties': properties,
        'can_edit_space': True,
    }
    return render(request, 'spaces/space-questions.html', context)


@login_required
def view_user_spaces_latest_questions(request):
    user_spaces = (SpaceMember.objects
                   .filter(user=request.user)
                   .values_list('space_id', flat=True)
                   .order_by('-created_at')[:3])
    tab = utils.get_request_tab(request)
    q = utils.get_request_param(request, 'q', None)
    tag_word = utils.get_request_param(request, 'tag', None)
    spaces_base_qs = Question.objects.filter(space__in=user_spaces, space__restricted=True)
    if tag_word:
        spaces_base_qs = spaces_base_qs.filter(Q(tags__tag_word__iexact=tag_word))
    spaces_questions_qs = _get_questions_queryset(spaces_base_qs, tab, q, None)
    spaces_questions_qs = spaces_questions_qs[:5]

    context = {
        'query': q,
        'has_results': spaces_questions_qs.count() > 0,
        'tag_word': tag_word,
        'space_questions': spaces_questions_qs,
    }
    return render(request, 'spaces/includes/user-spaces-questions.partial.html', context)
