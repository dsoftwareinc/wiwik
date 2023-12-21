from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render

from forum.views import utils
from spaces.models import Space


@login_required
def view_side_menu_user_spaces(request):
    if request.method != "GET":
        raise Http404()
    if request.user.is_superuser:
        spaces = Space.objects.all().order_by("-created_at")
    else:
        spaces = Space.objects.filter(spacemember__user=request.user).order_by("-created_at")
    return render(
        request,
        "spaces/base.menu.spaces.partial.html",
        {
            "spaces": spaces,
            "calling_url": utils.get_request_param(request, "calling_url", None),
        },
    )
