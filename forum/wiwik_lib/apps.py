import logging

from django.apps import AppConfig

logger = logging.getLogger(__package__)


class LibConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wiwik_lib'
