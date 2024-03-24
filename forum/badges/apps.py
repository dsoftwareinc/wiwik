import logging
import sys

from django.apps import AppConfig

"""
Module handling all badges related logic.

upsert_badges_in_db() -
    creates badges in database and update them if needed based on BADGE_MAP
    values.

review_all_badges()
    Check for all badges in BADGE_MAP for every user whether the user earned
    it or not.

check_badge_for_all_users(badge)
    Entitle users who deserve a specific Badge.

check_all_badges_for_user(user)
    Entitle a user with all badges they deserve.

"""
logger = logging.getLogger(__package__)


class BadgesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "badges"

    def ready(self):
        pass
