from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from forum import models
from forum.apps import logger
from wiwik_lib.views.follow_views import delete_follow, create_follow


@login_required
def view_follow_question(request, pk: int):
    user = request.user
    q = models.Question.objects.filter(pk=pk).first()
    if q is None:
        logger.warning(
            f"user {user.username} trying to follow question {pk} which does not exist"
        )
        return redirect("forum:list")
    create_follow(q, user)
    return redirect("forum:thread", pk=pk)


@login_required
def view_unfollow_question(request, pk: int):
    user = request.user
    q = models.Question.objects.filter(pk=pk).first()
    if q is None:
        logger.warning(
            f"user {user.username} trying to unfollow question {pk} which does not exist"
        )
        return redirect("forum:list")
    follow = q.follows.filter(user=user).first()
    if follow is None:
        logger.warning(
            f"user {user.username} asked to unfollow question {pk} even "
            f"though they are not currently following it"
        )
    delete_follow(q, user)
    return redirect("forum:thread", pk=pk)
