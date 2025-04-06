from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from wiwik_lib.advanced_model_manager import AdvancedModelManager


class VoteActivity(models.Model):
    """
    This model represents an activity related to a target user.
    Either a reputation change (upvote/downvote/accepted answer/edit content)
    or getting a badge from the system.
    """

    class ActivityType(models.TextChoices):
        UPVOTE = "u", "Upvote"
        DOWNVOTE = "d", "Downvote"
        ACCEPT = "a", "Accepted answer"
        EDITED = "e", "Edited post"
        ACCEPT_OLD = "o", "Accepted answer for old question"
        BADGE = "b", "Badge"

    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(
        max_length=2,
        choices=ActivityType.choices,
        default=ActivityType.UPVOTE,
        help_text="Vote activity type",
    )
    source = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.DO_NOTHING,
        help_text="User who voted to create this activity",
        related_name="+",
    )
    target = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User affected by this activity",
        related_name="reputation_votes",
    )
    question = models.ForeignKey(
        "forum.Question",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        help_text="Question caused this",
    )
    answer = models.ForeignKey(
        "forum.Answer",
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
        help_text="Answer that caused this, if relevant",
    )
    reputation_change = models.IntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="Change in reputation for target user",
    )
    seen = models.DateTimeField(
        default=None,
        null=True,
        blank=True,
        help_text="When the target user has seen this activity",
    )
    badge = models.ForeignKey(
        "badges.Badge",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        default=None,
        help_text="Badge on this activity",
    )
    objects = AdvancedModelManager(
        select_related=(
            "badge",
            "target",
            "question",
        ),
    )

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        if self.badge:
            return f"{self.target.username} earned {self.badge.name}"
        answer_str = f" answer {self.answer_id}" if self.answer is not None else ""
        return f"VoteActivity[{self.reputation_change},target={self.target.username},q={self.question_id}{answer_str}]"

    @property
    def time_section(self):
        curr_time = timezone.now()
        if self.created_at.date() == curr_time.date():
            section = "Today"
        elif self.created_at >= curr_time - timedelta(days=7):
            section = "Last 7 days"
        elif self.created_at >= curr_time - timedelta(days=30):
            section = "Last 30 days"
        else:
            section = "Older"
        return section

    def save(self, *args, **kwargs):
        update_last_activity = self.id is None
        super(VoteActivity, self).save(*args, **kwargs)
        if update_last_activity and (self.question or self.answer):
            q = self.question or self.answer.get_question()
            q.last_activity = self.created_at
            q.save()


class SearchRecord(models.Model):
    """
    This model represents a search done on the server.
    The information can be used for reporting.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="User affected by this activity",
        related_name="+",
    )
    query = models.CharField(max_length=400, help_text="Query user did")
    results = models.CharField(max_length=50, help_text="questionIds results")
    time = models.IntegerField(help_text="Time search has taken")

    def __str__(self):
        return f"SearchRecord[query={self.query}]"
