from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from wiwik_lib.utils import paginate_queryset
from forum.models import UserTagStats
from tags import models


def get_user_followed_tags(user: AbstractUser):
    if 'forum' not in settings.INSTALLED_APPS:
        return []
    follows = UserTagStats.objects.filter(user=user)
    return [f.tag.tag_word for f in follows]


def render_tags_list(request):
    query = request.GET.get('q', None)
    basic_query_set = (models.Tag.objects.all())

    if query:
        basic_query_set = (basic_query_set
                           .filter(Q(tag_word__icontains=query) | Q(synonym__name__icontains=query)))
    basic_query_set = basic_query_set.order_by('-number_of_questions', 'tag_word')

    # Pagination
    page = request.GET.get('page', 1)
    filtered_tags = paginate_queryset(basic_query_set, page, 12)
    tag_user_follows = get_user_followed_tags(request.user)
    return loader.render_to_string('tags/tags-list.html', {
        "tags": filtered_tags,
        "query": query,
        "tags_watched": tag_user_follows,
        "count": basic_query_set.count(),
        'title': 'wiwik - Tags',
    })


@login_required
def view_query(request):
    return HttpResponse(render_tags_list(request))


@login_required
def view_home(request):
    content = render_tags_list(request)
    return render(request, 'tags/tags.html', {'content': content, })
