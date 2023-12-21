from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from spaces import models


@login_required
def view_property_info(request, property_name: str):
    if request.method != "GET":
        raise Http404()
    prop = get_object_or_404(models.SpaceProperty, name=property_name)

    return render(
        request,
        "spaces/property.single.template.html",
        {
            "property": prop,
            "spaces_count": prop.spaces.all().count(),
            "spaces": prop.spaces.all().order_by("-created_at"),
        },
    )
