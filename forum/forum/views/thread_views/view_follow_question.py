from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from forum import models
from forum.apps import logger
from forum.views import follow_models


@login_required
def view_follow_question(request, pk: int):
    user = request.user
    q = models.Question.objects.filter(pk=pk).first()
    if q is None:
        logger.warning(f'user {user.username} trying to follow question {pk} which does not exist')
        return redirect('forum:list')
    follow_models.create_follow_question(q, user)
    return redirect('forum:thread', pk=pk)


@login_required
def view_unfollow_question(request, pk: int):
    user = request.user
    q = models.Question.objects.filter(pk=pk).first()
    if q is None:
        logger.warning(f'user {user.username} trying to unfollow question {pk} which does not exist')
        return redirect('forum:list')

    follow = models.QuestionFollow.objects.filter(user=user, question=q).first()
    if follow is None:
        logger.warning(f'user {user.username} asked to unfollow question {pk} even '
                       f'though they are not currently following it')
    follow_models.delete_follow_question(q, user)
    return redirect('forum:thread', pk=pk)
