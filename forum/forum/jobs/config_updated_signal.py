from typing import Any

from constance.signals import config_updated
from django.dispatch import receiver

from tags.jobs import update_tag_stats
from wiwik_lib.templatetags.wiwik_template_tags import check_latex_config
from .base import start_job
from .calculate_user_tag_stats import recalculate_user_reputation_score
from .moderator_check import update_moderator_status_for_users, warn_users_loosing_moderator_status
from .user_impact import calculate_all_users_impact


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs: Any) -> None:  # type: ignore
    if key in {"NUMBER_OF_TAG_EXPERTS", "NUMBER_OF_TAG_RISING_STARS"}:
        start_job(update_tag_stats)
    elif key in {
        "UPVOTE_CHANGE",
        "DOWNVOTE_CHANGE",
        "ACCEPT_ANSWER_CHANGE",
        "ACCEPT_ANSWER_OLD_QUESTION_CHANGE",
        "EDITED_CHANGE",
    }:
        start_job(recalculate_user_reputation_score)
        start_job(calculate_all_users_impact)
    elif key in {
        "DAYS_TO_REVOKE_MODERATOR",
        "DAYS_TO_GRANT_MODERATOR",
    }:
        start_job(update_moderator_status_for_users)
        start_job(warn_users_loosing_moderator_status)
    elif key in {"LATEX_SUPPORT_ENABLED"}:
        check_latex_config()
