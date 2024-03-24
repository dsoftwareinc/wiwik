import logging

from django.apps import AppConfig
from django.core.checks import Warning, register

logger = logging.getLogger(__package__)


class ForumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forum"

    def ready(self):
        pass


@register()
def wiwik_check_config(app_configs, **kwargs):
    from constance import config
    from django.conf import settings

    errors = []
    if config.GOOGLE_ANALYTICS_KEY is None:
        errors.append(Warning(
            "Google Analytics key is not configured! set environment variable GOOGLE_ANALYTICS_KEY",
            hint="Set environment variable GOOGLE_ANALYTICS_KEY",
            obj=config,
            id="forum.E001",
        ))
    if not settings.ADMINS:
        errors.append(Warning(
            "email for admin is not configured! set environment variable ADMIN_EMAIL",
            hint="Set environment variable ADMIN_EMAIL",
            obj=settings,
            id="forum.E002",
        ))
    return errors
