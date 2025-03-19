import logging
import sys

from django.apps import AppConfig


logger = logging.getLogger(__package__)


class LibConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wiwik_lib"

    def ready(self):
        if 'runserver' not in sys.argv:
            return
        from wiwik_lib.utils import set_current_site
        set_current_site()
