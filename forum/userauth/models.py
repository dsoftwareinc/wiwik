from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from userauth.apps import logger


class ForumUserManager(UserManager):
    def get_queryset(self, *args, **kwargs):
        qs = super(ForumUserManager, self).get_queryset(*args, **kwargs)
        # qs = qs.select_related('additional_data')
        return qs


class ForumUser(AbstractUser):
    email = models.EmailField(verbose_name="email address", max_length=255, unique=True)
    name = models.CharField(max_length=100, null=True, blank=True, help_text="User displayed name")
    title = models.CharField(
        max_length=100,
        default="",
        null=True,
        blank=True,
        help_text="Title of user at work, etc.",
    )
    about_me = models.TextField(default=None, null=True, blank=True)
    profile_pic = models.ImageField(
        upload_to="user_pics",
        default="default_pics/default_image.jpg",
        blank=True,
        null=True,
    )
    github_handle = models.CharField(
        max_length=39,
        default=None,
        null=True,
        blank=True,
        help_text="User github handle",
    )
    keybase_user = models.CharField(
        max_length=16,
        default=None,
        null=True,
        blank=True,
        help_text="User github handle",
    )
    date_joined = models.DateTimeField(default=timezone.now)
    USERNAME_FIELD = "username"
    is_moderator = models.BooleanField(
        _("moderator status"),
        default=False,
        help_text=_("Designates whether the user can moderate other user Q&A."),
    )
    slack_userid = models.CharField(
        max_length=25,
        default=None,
        null=True,
        blank=True,
        help_text="Slack user id",
        unique=True,
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text=_("email notifications enabled?"),
    )
    objects = ForumUserManager()
    reputation_score = models.IntegerField(default=0)
    search_count = models.IntegerField(default=0, help_text="Number of searches user made")
    bookmarks_count = models.IntegerField(default=0, help_text="Number of bookmarks user have")
    last_email_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date+Time of email sent to user",
    )
    bronze_badges = models.IntegerField(default=0, help_text="Number of bronze badges the user has")
    silver_badges = models.IntegerField(default=0, help_text="Number of silver badges the user has")
    gold_badges = models.IntegerField(default=0, help_text="Number of gold badges the user has")
    next_badge = models.ForeignKey(
        "badges.Badge",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Next badge recommended for user",
    )

    people_reached = models.IntegerField(default=0, help_text="Number of views posts user created had")
    posts_edited = models.IntegerField(default=0, help_text="Number of posts user edited")
    votes = models.IntegerField(default=0, help_text="Number of votes user casted")

    def display_name(self):
        return self.name if self.name else self.email

    @property
    def badges(self):
        return [self.bronze_badges, self.silver_badges, self.gold_badges]

    def has_perm(self, perm, obj=None):
        if not self.is_active:
            return False
        if self.is_superuser:
            return True
        if perm in {
            "question_edit",
            "question_delete",
            "article_edit",
            "article_delete",
            "article_create",
            "answer_edit",
            "answer_delete",
            "comment_delete",
            "tag_edit",
            "synonym_approve",
        }:
            return self.is_staff or self.is_moderator
        logger.warning(f"Asked for permission {perm} - something is going on")
        return False

    @property
    def can_edit(self):
        return self.is_staff or self.is_moderator

    @property
    def can_delete_question(self):
        return self.is_staff or self.is_moderator

    @property
    def can_delete_answer(self):
        return self.is_staff or self.is_moderator

    @property
    def can_delete_comment(self):
        return self.is_staff or self.is_moderator

    @property
    def can_edit_tag(self):
        return self.is_staff or self.is_moderator

    @property
    def can_approve_synonym(self):
        return self.is_staff or self.is_moderator

    def __str__(self):
        return f"User[{self.username}]"


class ForumUserAdditionalData(models.Model):
    user = models.OneToOneField(ForumUser, on_delete=models.CASCADE, blank=False)
    reputation_score = models.IntegerField(default=0)
    search_count = models.IntegerField(default=0, help_text="Number of searches user made")
    bookmarks_count = models.IntegerField(default=0, help_text="Number of bookmarks user have")
    last_email_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date+Time of email sent to user",
    )
    bronze_badges = models.IntegerField(default=0, help_text="Number of bronze badges the user has")
    silver_badges = models.IntegerField(default=0, help_text="Number of silver badges the user has")
    gold_badges = models.IntegerField(default=0, help_text="Number of gold badges the user has")
    next_badge = models.ForeignKey(
        "badges.Badge",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="Next badge recommended for user",
    )

    people_reached = models.IntegerField(default=0, help_text="Number of views posts user created had")
    posts_edited = models.IntegerField(default=0, help_text="Number of posts user edited")
    votes = models.IntegerField(default=0, help_text="Number of votes user casted")

    class Meta:
        default_related_name = "additional_data"


class UserVisit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    visit_date = models.DateField()
    consecutive_days = models.IntegerField(default=1)
    max_consecutive_days = models.IntegerField(default=1)
    total_days = models.IntegerField(default=1)
    ip_addr = models.CharField(max_length=30, null=True, blank=True)
    country = models.CharField(max_length=40, null=True, blank=True)
    city = models.CharField(max_length=40, null=True, blank=True)

    class Meta:
        unique_together = ("user", "visit_date", "ip_addr")
        verbose_name_plural = "User visits"

    def __str__(self):
        return f"UserVisit[user={self.user.username},date={self.visit_date}]"


@receiver(post_save, sender=ForumUser)
def create_additional_data_for_user(sender, instance, created, **kwargs):
    if created:
        ForumUserAdditionalData.objects.create(user=instance)
