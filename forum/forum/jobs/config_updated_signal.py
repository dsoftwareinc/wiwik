from constance.signals import config_updated
from django.dispatch import receiver

from .base import start_job
from .user_impact import calculate_all_users_impact
from .moderator_check import update_moderator_status_for_users,warn_users_loosing_moderator_status
from .calculate_user_tag_stats import recalculate_user_reputation_score
from tags.jobs import update_tag_stats


@receiver(config_updated)
def constance_updated(sender, key, old_value, new_value, **kwargs):
    if key in {"NUMBER_OF_TAG_EXPERTS", "NUMBER_OF_TAG_RISING_STARS"}:
        start_job(update_tag_stats)
    elif key in {
        "UPVOTE_CHANGE", "DOWNVOTE_CHANGE", "ACCEPT_ANSWER_CHANGE",
        "ACCEPT_ANSWER_OLD_QUESTION_CHANGE", "EDITED_CHANGE"
    }:
        start_job(recalculate_user_reputation_score)
        start_job(calculate_all_users_impact)
    elif key in {"DAYS_TO_REVOKE_MODERATOR", "DAYS_TO_GRANT_MODERATOR", }:
        start_job(update_moderator_status_for_users)
        start_job(warn_users_loosing_moderator_status)
