from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def view_partial_user_navbar(request):
    return render(
        request,
        'includes/partial.user.navbar.html',
    )
