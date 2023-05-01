from django.contrib import messages
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from userauth.models import ForumUser
from userauth.views.tokens import account_activation_token


def view_unsubscribe(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = ForumUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, ForumUser.DoesNotExist) as e:  # noqa: F841
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.email_notifications = False
        user.save()
        return redirect('userauth:login')
    else:
        messages.error(request, 'Unsubscribe link is invalid!', 'danger')
        return redirect('userauth:login')
