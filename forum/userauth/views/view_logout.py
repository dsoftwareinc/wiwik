from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def view_logout(request):
    logout(request)
    messages.info(request, "Logged out successfully!")
    return redirect(settings.LOGIN_URL)
