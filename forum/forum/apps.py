import logging

from django.conf import settings
from django.apps import AppConfig

logger = logging.getLogger(__package__)


class ForumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forum"

    def ready(self):
        from constance import config

        if config.GOOGLE_ANALYTICS_KEY is None:
            logger.warning("Google Analytics key is not configured! set environment variable GOOGLE_ANALYTICS_KEY")
        if not settings.ADMINS:
            logger.warning("email for admin is not configured! set environment variable ADMIN_EMAIL")
