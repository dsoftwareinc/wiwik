from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from forum.apps import logger
from forum.views import utils


@login_required
def view_deletecomment(request, pk: int, model: str, comment_id: int):
    comment = utils.get_model('comment_' + model, comment_id)
    user = request.user
    if comment is None:
        logger.warning(f'user {user.username} tried to delete comment {comment_id} which does not exist')
        return redirect('forum:thread', pk=pk)
    parent_pk = comment.answer.pk if model == 'answer' else comment.question.pk
    if comment.author == user or user.can_delete_comment:
        utils.delete_comment(comment)
        messages.success(request, "Comment deleted")
    anchor = f'#{model}_{parent_pk}'
    return redirect(reverse('forum:thread', args=[pk]) + anchor)
