from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.shortcuts import redirect
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from userauth.views.tokens import account_activation_token

User = get_user_model()


def view_activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:  # noqa: F841
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        messages.success(
            request,
            "Account activated successfully. Thank you for your email confirmation. Now you can login your account.",
        )
        return redirect("userauth:login")
    else:
        messages.error(request, "Activation link is invalid!", "danger")
        return redirect("userauth:login")
