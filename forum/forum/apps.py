import logging

from django.apps import AppConfig
from django.core.checks import Warning, register


logger = logging.getLogger(__package__)


@register()
def wiwik_check_config(app_configs, **kwargs):
    from constance import config
    from django.conf import settings

    logger.info("Checking Google Analytics key and admin email is configured")
    errors = []
    if config.GOOGLE_ANALYTICS_KEY is None:
        logger.warning("Google Analytics key is not configured! set it in the admin console")
        errors.append(Warning(
            "Google Analytics key is not configured! set environment variable GOOGLE_ANALYTICS_KEY",
            hint="Set environment variable GOOGLE_ANALYTICS_KEY",
            obj=config,
            id="forum.E001",
        ))
    if not settings.ADMINS:
        logger.warning("email for admin is not configured! set it as environment variable ADMIN_EMAIL")
        errors.append(Warning(
            "email for admin is not configured! set environment variable ADMIN_EMAIL",
            hint="Set environment variable ADMIN_EMAIL",
            obj=settings,
            id="forum.E002",
        ))

    return errors


class ForumConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "forum"

    def ready(self):
        from wiwik_lib.templatetags.wiwik_template_tags import check_latex_config
        from forum.integrations.slack_api import configure_slack_client

        check_latex_config()
        configure_slack_client()
