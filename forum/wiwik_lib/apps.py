import logging

import pymdownx.arithmatex as arithmatex

from django.apps import AppConfig
from django.core import checks


logger = logging.getLogger(__package__)

@checks.register()
def check_latex_support(app_configs, **kwargs):
    messages = []
    from constance import config
    if not config.LATEX_SUPPORT_ENABLED:
        return messages
    from wiwik_lib.templatetags.wiwik_template_tags import MARKDOWN_EXTENSIONS_CONFIG
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.arithmatex"] = {
        "generic": True,
    }
    MARKDOWN_EXTENSIONS_CONFIG["pymdownx.superfences"]["custom_fences"].append(
        {
            "name": "math",
            "class": "arithmatex",
            "format": arithmatex.fence_generic_format,
        }
    )
    messages.append(checks.Info(
        "LaTeX support is enabled",
    ))
    return messages

class LibConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "wiwik_lib"

    def ready(self):
        pass