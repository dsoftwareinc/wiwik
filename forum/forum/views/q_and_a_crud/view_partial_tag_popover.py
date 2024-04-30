from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from tags.models import Tag


@login_required
def view_partial_tag_popover(request, pk):
    tag = Tag.objects.get(pk=pk)
    return render(request, "main/includes/partial.questions-list.tag-popover.html", {"t": tag})