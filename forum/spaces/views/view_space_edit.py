from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from forum.models import Question
from spaces.apps import logger
from spaces.models import Space
from spaces.views.access import validate_space_access
from userauth.models import ForumUser


@login_required
def view_space_edit(request, space_id: int):
    space = get_object_or_404(Space, id=space_id)
    validate_space_access(space, request.user)
    is_member = space.spacemember_set.filter(user=request.user).exists()
    if request.method == "GET":
        member_usernames = ",".join(space.spacemember_set.all().values_list("user__username", flat=True))
        latest_posts = Question.objects.filter(space=space).order_by("-created_at")[:5]

        return render(
            request,
            "spaces/space-edit.html",
            {
                "space": space,
                "is_member": is_member,
                "member_usernames": member_usernames,
                "latest_posts": latest_posts,
            },
        )
    if request.method != "POST":
        logger.warning(f"User {request.user} performed unexpected request method: {request.method}")
        return redirect("spaces:detail", space_id=space_id)
    # Save changes
    data = request.POST.dict()
    if "startDate" in data and data.get("startDate") != "":
        try:
            start_date = datetime.fromisoformat(data.get("startDate")).date()
            space.start_date = start_date
        except ValueError:
            pass
    if "endDate" in data and data.get("endDate") != "":
        try:
            end_date = datetime.fromisoformat(data.get("endDate")).date()
            space.end_date = end_date
        except ValueError:
            pass
    members = data.get("members")
    if members:
        member_usernames = members.split(",")
        space.spacemember_set.exclude(user__username__in=member_usernames).delete()
        for username in member_usernames:
            user = ForumUser.objects.filter(username=username).first()
            if user is None:
                continue
            space.spacemember_set.get_or_create(user=user)
    space.page = data.get("page") or space.page
    space.save()
    return redirect("spaces:detail", space_id=space_id)
