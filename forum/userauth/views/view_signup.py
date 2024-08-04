from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, mail_admins
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from userauth.apps import logger
from userauth.models import ForumUser
from userauth.views.tokens import account_activation_token
from wiwik_lib import utils
from wiwik_lib.adapters import inform_admins_bad_registration


class SignUpForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=254, help_text="Required. Inform a valid email address.")

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if ForumUser.objects.filter(email=email).exists():
            raise ValidationError(
                "email already registered, you can reset your password",
                code="email_exists",
            )
        allowed = utils.is_email_allowed(email)
        if not allowed:
            inform_admins_bad_registration(email, request=None)
            raise ValidationError(
                "email domain not allowed",
                code="email_domain_forbidden",
            )
        return email

    class Meta:
        model = ForumUser
        fields = (
            "username",
            "name",
            "email",
            "password1",
            "password2",
        )


def view_signup(request):
    if request.method == "GET":
        if isinstance(request.user, AnonymousUser):
            form = SignUpForm()
            return render(request, "userauth/signup.html", {"form": form})
        # User already logged in
        return redirect("forum:list")
    if request.method != "POST":
        logger.warning(f"User trying to use signup with HTTP {request.method}")
        return redirect("forum:list")

    form = SignUpForm(request.POST)
    if not form.is_valid():
        errors = form.errors.as_data()
        for key in errors:
            for validation_error in errors[key]:
                messages.error(request, validation_error.messages[0], "danger")
        return render(
            request=request,
            template_name="userauth/signup.html",
            context={"form": form},
        )

    user = form.save(commit=False)
    user.is_active = False
    user.save()

    mail_subject = "Activate your forum account"
    message = render_to_string(
        "emails/user_active_email.html",
        {
            "username": user.display_name(),
            "domain": utils.CURRENT_SITE,
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": account_activation_token.make_token(user),
        },
    )
    to_email = form.cleaned_data.get("email")
    email = EmailMessage(mail_subject, message, to=[to_email])
    email.send()
    username = form.cleaned_data.get("username")
    messages.success(
        request,
        f"New account created: {username}, " f"Please confirm your email address to complete the registration",
    )

    mail_admins(
        f"{to_email} registered to {utils.CURRENT_SITE}",
        f"{to_email} registered to {utils.CURRENT_SITE}",
    )
    return redirect("forum:home")
