from django.conf import settings
from django.db import models

from wiwik_lib.advanced_model_manager import AdvancedModelManager
from wiwik_lib.models import user_model_defer_fields


class UserTagStats(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    tag = models.ForeignKey("tags.Tag", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)
    questions_by_user = models.IntegerField(
        default=0,
        help_text="Number of questions authored by user in the tag",
    )
    answers_by_user = models.IntegerField(
        default=0,
        help_text="Number of answers authored by user in the tag",
    )
    reputation = models.IntegerField(default=0, help_text="Reputation earned by user for tag")
    reputation_last_month = models.IntegerField(
        default=0,
        help_text="Reputation earned by user for tag in the past month",
    )
    objects = AdvancedModelManager(
        select_related=(
            "user",
            "tag",
        ),
        deferred_fields=user_model_defer_fields("user"),
    )

    def __str__(self):
        return (
            f"UserTagStats[{self.user.username} - {self.tag.tag_word}] "
            f"#q={self.questions_by_user}, #a={self.answers_by_user}, "
            f"rep={self.reputation}, rep_month={self.reputation_last_month}"
        )
