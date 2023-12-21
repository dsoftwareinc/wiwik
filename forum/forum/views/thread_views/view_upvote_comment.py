from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from forum.apps import logger
from forum.views import utils


@login_required
def view_upvote_comment(request, pk: int, parent_model_name: str, comment_pk: int):
    user = request.user
    comment = utils.get_model("comment_" + parent_model_name, comment_pk)
    if comment.author == request.user:
        logger.info(f"user {user.username} tries to vote on their own input")
        return redirect("forum:thread", pk=pk)

    if comment.users_upvoted.filter(id=user.id).count() > 0:
        logger.debug(f"User {user.username} already upvoted")
        return redirect("forum:thread", pk=pk)

    utils.upvote_comment(user, comment)
    logger.debug(f"Upvote succeeded {user.username}:comment_{parent_model_name}:{comment_pk}")
    parent_pk = comment.answer.pk if parent_model_name == "answer" else comment.question.pk
    anchor = f"#{parent_model_name}_{parent_pk}"
    return redirect(reverse("forum:thread", args=[pk]) + anchor)
