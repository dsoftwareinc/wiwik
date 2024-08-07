from constance import config
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404

from forum.models import Question, Answer


@login_required
def view_partial_post_comments(request, post_type: str, post_pk: int):
    if post_type == "question":
        item = get_object_or_404(Question, pk=post_pk)
    elif post_type == "answer":
        item = get_object_or_404(Answer, pk=post_pk)
    else:
        return HttpResponseBadRequest("Post type not recognizable")
    num_comments = item.comments.count()
    return render(
        request,
        "main/includes/partial.thread.comments.template.html",
        {
            "item": item,
            "num_comments": num_comments,
            "max_comments": config.MAX_COMMENTS,
            "model": post_type,
            "comments": item.comments.all(),
        },
    )
