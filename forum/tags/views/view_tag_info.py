from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from forum.models import UserTagStats
from tags import models


@login_required
def view_tag_info(request, tag_word: str):
    if request.method != "GET":
        raise Http404()
    tag = get_object_or_404(models.Tag, tag_word=tag_word)
    tag_followers = UserTagStats.objects.filter(tag=tag, user__is_active=True).order_by(
        "-created_at"
    )
    synonyms = tag.synonym_set.filter(active=True)
    return render(
        request,
        "tags/tag-info.html",
        {
            "tag": tag,
            "can_edit_tag": True,
            "synonyms": synonyms,
            "followers": tag_followers,
        },
    )
