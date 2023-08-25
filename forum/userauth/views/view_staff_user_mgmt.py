from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404

from userauth.models import ForumUser


@login_required
def view_deactivate_user(request, username: str):
    if (not request.user.is_staff
            or request.method != 'GET'
            or request.user.username == username):
        raise PermissionDenied()
    u = get_object_or_404(ForumUser, username=username)
    u.is_active = False
    u.save()
    return redirect('userauth:profile', username=u.username, tab='questions')


@login_required
def view_activate_user(request, username: str):
    if (not request.user.is_staff
            or request.method != 'GET'
            or request.user.username == username):
        raise PermissionDenied()
    u = get_object_or_404(ForumUser, username=username)
    u.is_active = True
    u.save()
    return redirect('userauth:profile', username=u.username, tab='questions')
