from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from spaces.models import Space


@login_required
def view_space_leave(request, space_id: int):
    space = get_object_or_404(Space, id=space_id)
    if space.spacemember_set.filter(user=request.user).exists():
        space.member_remove(request.user)
    else:
        messages.info(request, f'You are not a member of {space.name}')
    return redirect('spaces:detail', space_id=space_id)


@login_required
def view_space_join(request, space_id: int):
    space = get_object_or_404(Space, id=space_id)
    if space.spacemember_set.filter(user=request.user).exists():
        messages.info(request, f'You are already a member of {space.name}')
    else:
        space.member_add(request.user)
    return redirect('spaces:detail', space_id=space_id)
