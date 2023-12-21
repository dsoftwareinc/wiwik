from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from forum.models import Answer
from forum.views import utils
from userauth.models import ForumUser
from wiwik_lib.views import ask_to_edit_resource, finish_edit_resource


@login_required
def view_editanswer(request, answer_pk):
    user = cast(ForumUser, request.user)
    answer = get_object_or_404(Answer, pk=answer_pk)
    if answer.author != user and not user.can_edit:  # TODO change edit user permissions
        messages.error(request, "You can not edit this answer", "danger")
        return redirect("forum:thread", pk=answer.question.pk)
    if not ask_to_edit_resource(request.user, answer):
        messages.warning(request, "Answer is currently edited by a different user")
        return redirect("forum:thread", pk=answer.question.pk)
    if request.method == "GET":
        return render(
            request,
            "main/editanswer.html",
            {
                "question": answer.question,
                "content": answer.content,
                "answer_pk": answer_pk,
            },
        )
    # Update answer
    req_dict = request.POST.dict()
    content = req_dict.get("queseditor")
    finish_edit_resource(answer)
    if content is None or content.strip() == "":
        messages.warning(request, "Can not erase answer content")
        return redirect(reverse("forum:thread", args=[answer.question.pk]) + f"#answer_{answer_pk}")
    utils.update_answer(request.user, answer, content)
    messages.success(request, "Answer updated successfully")
    return redirect(reverse("forum:thread", args=[answer.question.pk]) + f"#answer_{answer_pk}")
