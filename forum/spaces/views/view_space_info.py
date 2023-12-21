from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, get_object_or_404

from forum.models import Question
from spaces import models
from spaces.views.access import validate_space_access


@login_required
def view_space_info(request, space_id: int):
    if request.method != "GET":
        raise Http404()
    space = get_object_or_404(models.Space, id=space_id)
    validate_space_access(space, request.user)
    is_member = space.spacemember_set.filter(user=request.user).exists()
    members = space.spacemember_set.all()
    properties = space.properties.all()
    latest_posts = Question.objects.filter(space=space).order_by("-created_at")[:5]

    posts_count = Question.objects.filter(space=space).count()

    return render(
        request,
        "spaces/space-info.html",
        {
            "space": space,
            "is_member": is_member,
            "members": members,
            "latest_posts": latest_posts,
            "posts_count": posts_count,
            "properties": properties,
        },
    )
