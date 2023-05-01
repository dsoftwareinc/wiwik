from django import forms
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage, mail_admins
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from wiwik_lib.utils import is_email_allowed
from wiwik_lib.adapters import inform_admins_bad_registration
from userauth.models import ForumUser
from userauth.views.tokens import account_activation_token


class SignUpForm(UserCreationForm):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if ForumUser.objects.filter(email=email).exists():
            raise ValidationError(
                'email already registered, you can reset your password',
                code="email_exists",
            )
        allowed = is_email_allowed(email)
        if not allowed:
            inform_admins_bad_registration(email, request=None)
            raise ValidationError(
                'email domain not allowed',
                code="email_domain_forbidden",
            )
        return email

    class Meta:
        model = ForumUser
        fields = ('username', 'name', 'email', 'password1', 'password2',)


def view_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Activate your forum account'
            domain = current_site.domain
            if not domain.startswith('http://') and not domain.startswith('https://'):
                domain = 'http://' + domain
            message = render_to_string('emails/user_active_email.html', {
                'username': user.display_name(),
                'domain': domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            username = form.cleaned_data.get('username')

            site = get_current_site(request)
            msg = f'{to_email} registered to {site.domain}'
            mail_admins(msg, msg)
            messages.success(
                request,
                f"New account created: {username}, "
                f"Please confirm your email address to complete the registration")
            return redirect('forum:home')
        else:
            errors = form.errors.as_data()
            for key in errors:
                for validation_error in errors[key]:
                    messages.error(request, validation_error.messages[0], 'danger')
            return render(request=request, template_name="userauth/signup.html", context={"form": form})
    # Get request
    if isinstance(request.user, AnonymousUser):
        form = SignUpForm()
        return render(request, 'userauth/signup.html', {'form': form})
    else:
        return redirect('forum:list')
