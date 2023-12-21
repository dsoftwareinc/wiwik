from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import render, redirect

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from forum import jobs
from userauth.apps import logger


@login_required
def view_editprofile(request):
    def set_val(
        key: str, attribute: str, min_length: int = 1, max_length: int = 20_000
    ):
        val = data.get(key, None)
        if not val:
            return
        if min_length and max_length and min_length <= len(val) <= max_length:
            setattr(user, attribute, val)
        else:
            msg = f"Expected value length between {min_length}..{max_length} for {key} but got {len(val)}"
            logger.warn(msg)
            raise SuspiciousOperation(msg)

    user = request.user
    if request.method == "POST":
        data = request.POST.dict()
        try:
            set_val("fullname", "name", 1, 100)
            set_val("about", "about_me")
            set_val("title", "title", 1, 100)
            set_val("github_handle", "github_handle", 1, 39)
            set_val("keybase_user", "keybase_user", 1, 16)
            user.email_notifications = data.get("email_notifications") == "on"
            user.save()
            messages.success(request, "Profile updated successfully")
            jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Edit profile"])
            return redirect("userauth:profile", username=user.username, tab="questions")
        except SuspiciousOperation as e:
            messages.error(request, e.args[0])

    return render(
        request,
        "userauth/editprofile.html",
        {
            "user": user,
            "title": "wiwik - Edit profile",
        },
    )
