from django.conf import settings
from django.db import models

from forum.models import Question
from wiwik_lib.advanced_model_manager import AdvancedModelManager
from wiwik_lib.models import user_model_defer_fields


class PostInvitation(models.Model):
    """Invite a user to participate in a post, answer question, comment on article, etc.
    This data will be shown in the post's data.
    While a question is left unanswered => the viewer can see who is invited to answer the question.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, related_name="invitations")
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AdvancedModelManager(select_related=("invitee",), deferred_fields=user_model_defer_fields("invitee"))

    class Meta:
        verbose_name_plural = "Post Invitations"

    def __str__(self):
        return f"PostInvitation[inviter={self.inviter.username},invitee={self.invitee.username}post={self.question.id}]"


class QuestionBookmark(models.Model):
    """
    Represents a bookmark of a user.
    """

    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, related_name="bookmarks")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)
    objects = AdvancedModelManager(
        select_related=("question",),
    )

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        super(QuestionBookmark, self).save(force_insert, force_update, using, update_fields)
        self.user.bookmarks_count = QuestionBookmark.objects.filter(user=self.user).count()
        self.user.save()

    def delete(self, using=None, keep_parents=False):
        super(QuestionBookmark, self).delete(using, keep_parents)
        self.user.bookmarks_count = QuestionBookmark.objects.filter(user=self.user).count()
        self.user.save()
