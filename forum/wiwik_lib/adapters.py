import django.core.mail
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from constance import config
from django.conf import settings
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import PermissionDenied

from wiwik_lib.utils import is_email_allowed


def inform_admins_bad_registration(email: str, request) -> None:
    from forum.views.notifications import notify_slack_channel

    site = get_current_site(request)
    subject = f"{email} tried to register to {site.domain}"
    django.core.mail.mail_admins(
        subject,
        subject,
    )
    notify_slack_channel(subject, config.SLACK_ADMIN_NOTIFICATIONS_CHANNEL)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        u = sociallogin.user
        allowed = is_email_allowed(u.email)
        if not allowed:
            messages.error(
                request,
                f"Only emails from {'; '.join(settings.ALLOWED_REGISTRATION_EMAIL_DOMAINS)} are allowed",
                "danger",
            )
            inform_admins_bad_registration(u.email, request)
            user_email_domain = u.email.split("@")[1]
            raise PermissionDenied(f"login failed with email from  @{user_email_domain} domain")
