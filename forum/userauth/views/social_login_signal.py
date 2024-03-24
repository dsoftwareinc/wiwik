import os

import urllib3
from allauth.account.signals import user_signed_up, user_logged_in
from constance import config
from django.core.files.base import ContentFile
from django.dispatch import receiver

from userauth.apps import logger
from userauth.models import ForumUser

http = urllib3.PoolManager()


def _populate_user_data_from_social(user: ForumUser, picture_only: bool = False) -> None:
    user_social_account = user.socialaccount_set.filter(provider="google").first()
    if user_social_account is None:
        logger.info(f"Could not find social account for user {user.username}")
        return
    user_data = user_social_account.extra_data
    picture_url = user_data.get("picture", None)
    if picture_url is not None:
        req = http.request("GET", picture_url)
        data = ContentFile(req.data)
        file_name = f"profile_pic_{user.username}.google.jpeg"
        user.profile_pic.save(file_name, data, save=True)
    if not picture_only and "email" in user_data:
        user.email = user_data["email"]
    if not picture_only and "name" in user_data:
        user.name = user_data["name"]
    user.save()


@receiver(user_signed_up)
def populate_profile(sociallogin, user: ForumUser, **kwargs):
    from forum.views.notifications import notify_slack_channel

    if sociallogin.account.provider != "google":
        return
    _populate_user_data_from_social(user)
    msg = f"User {user.display_name()} signed up to wiwik"
    notify_slack_channel(msg, config.SLACK_ADMIN_NOTIFICATIONS_CHANNEL)


@receiver(user_logged_in)
def fill_missing_data_in_profile(sociallogin, user: ForumUser, **kwargs):
    if sociallogin.account.provider != "google":
        return
    if os.path.isfile(user.profile_pic.path):
        return
    _populate_user_data_from_social(user, picture_only=True)
