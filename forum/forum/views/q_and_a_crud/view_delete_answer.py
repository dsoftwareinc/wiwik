from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from forum.apps import logger
from forum.models import Answer
from forum.views import utils
from userauth.models import ForumUser


@login_required
def view_delete_answer(request, question_pk: int, answer_pk: int):
    user: ForumUser = cast(ForumUser, request.user)
    question = utils.get_model("question", question_pk)
    answer: Answer = utils.get_model("answer", answer_pk)
    if answer is None:
        logger.warning(f"user {user.username} tried to delete answer {answer_pk} which does not exist")
        return redirect("forum:thread", pk=question_pk)

    if answer.question_id != question_pk:
        logger.warning(
            f"user {user.username} tried to delete answer {answer_pk} "
            f"for question {question_pk} but answer is for question {answer.question_id}"
        )
        return redirect("forum:thread", pk=question_pk)

    if answer.author != user and not user.can_delete_answer:
        logger.warning(f"user {user.username} tried to delete answer {answer_pk} which they did not author")
        return redirect("forum:thread", pk=question_pk)
    if request.method == "POST":
        utils.delete_answer(answer)
        messages.success(request, "Answer deleted")
        return redirect("forum:thread", pk=question_pk)
    # Get request
    return render(
        request,
        "main/deleteanswer.html",
        {
            "question": question,
            "question_pk": question_pk,
            "answer": answer,
            "answer_pk": answer_pk,
        },
    )
