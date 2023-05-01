from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from forum.views.follow_models import delete_follow_tag, create_follow_tag
from tags.models import Tag


@login_required
def view_user_follow_tag(request, tag_word):
    redirect_url = request.META.get('HTTP_REFERER', None) or reverse('forum:tag', args=[tag_word, ])
    tag = Tag.objects.filter(tag_word=tag_word).first()
    if tag is None:
        return redirect('forum:tag', tag_word=tag_word)
    create_follow_tag(tag, request.user)
    return redirect(redirect_url)


@login_required
def view_user_unfollow_tag(request, tag_word):
    redirect_url = request.META.get('HTTP_REFERER', None) or reverse('forum:tag', args=[tag_word, ])
    tag = Tag.objects.filter(tag_word=tag_word).first()
    if tag is None:
        return redirect('forum:tag', tag_word=tag_word)
    delete_follow_tag(tag, request.user)
    return redirect(redirect_url)
