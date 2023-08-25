import logging

from django.apps import AppConfig

logger = logging.getLogger(__package__)


class SimilarityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'similarity'
    verbose_name = 'Similar questions'
