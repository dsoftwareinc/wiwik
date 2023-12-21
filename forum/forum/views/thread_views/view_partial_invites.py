from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from forum.models import Question


@login_required
def view_partial_invites(request, question_pk: int):
    q = get_object_or_404(Question, pk=question_pk)
    latest_invitations = (
        q.invitations.all().select_related("invitee").order_by("-created_at")[:3] if not q.has_accepted_answer else []
    )

    return render(
        request,
        "main/includes/partial.thread.question-invitations.html",
        {"latest_invitations": latest_invitations},
    )
