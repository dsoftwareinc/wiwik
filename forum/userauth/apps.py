import logging

from django.apps import AppConfig

logger = logging.getLogger(__package__)


class UserauthConfig(AppConfig):
    name = "userauth"
