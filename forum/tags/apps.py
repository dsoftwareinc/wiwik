import logging

from django.apps import AppConfig

logger = logging.getLogger(__package__)


class TagsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tags"
