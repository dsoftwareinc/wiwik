from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from forum.apps import logger
from forum.views import utils


@login_required
def view_downvote(request, pk: int, model_name: str, model_pk: int):
    user = request.user
    model_obj = utils.get_model(model_name, model_pk)
    anchor = f'#{model_name}_{model_pk}'
    redirect_url = reverse('forum:thread', args=[pk]) + anchor
    if model_obj.author == user:
        logger.warning(f'user {user.username} tries to vote on their own input')
        messages.info(request, "You can't down vote your own posts")
        return redirect(redirect_url)

    if model_obj.users_downvoted.filter(id=user.id).count() > 0:
        logger.info(f'User {user.username} already downvoted, undoing')
        utils.undo_downvote(user, model_obj)
        return redirect(redirect_url)

    utils.downvote(user, model_obj)
    logger.debug(f"Downvote succeeded {user.username}:{model_name}:{model_pk}")
    return redirect(redirect_url)
