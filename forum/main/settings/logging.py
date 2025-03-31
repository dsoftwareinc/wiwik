# Logging
import logging
import os

from django.core.management.color import color_style

from .base import DEBUG


class ColorFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        super(ColorFormatter, self).__init__(*args, **kwargs)
        self.style = self.configure_style(color_style(DEBUG))

    def configure_style(self, style):
        style.DEBUG = style.HTTP_NOT_MODIFIED
        style.INFO = style.HTTP_INFO
        style.WARNING = style.HTTP_NOT_FOUND
        style.ERROR = style.ERROR
        style.CRITICAL = style.HTTP_SERVER_ERROR
        return style

    def format(self, record):
        message = logging.Formatter.format(self, record)
        colorizer = getattr(self.style, record.levelname, self.style.HTTP_SUCCESS)
        return colorizer(message)


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "()": "main.settings.ColorFormatter",
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "()": "main.settings.ColorFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s.%(funcName)s:%(lineno)s- %(message)s",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            # 'filters': ['require_debug_true'],
            # - print everything to console, gunicorn aggregates to file
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "root": {
        "handlers": ["console", "mail_admins"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "DEBUG"),
    },
    "loggers": {
        "scheduler": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "MARKDOWN": {
            "handlers": [
                "console",
            ],
            "level": "WARNING",
            "propagate": True,
        },
        "rq": {
            "handlers": [
                "console",
            ],
            "level": "INFO",
            "propagate": True,
        },
        # 'django.db.backends': {
        #     'handlers': ['console'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'badges': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'forum': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'tags': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'userauth': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'similarity': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'flags': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
        # 'main': {
        #     'handlers': ['console', 'mail_admins'],
        #     'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        # },
    },
}
