from datetime import timedelta, datetime
from typing import Optional

from constance import config
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import F, TextField
from django.db.models.signals import post_save
from django.urls import reverse
from django.utils import timezone

from common.utils import dedent_code
from forum.apps import logger
from spaces.models import Space
from tags.models import Tag
from wiwik_lib.models import Flaggable, Editable, Followable
from wiwik_lib.utils import CURRENT_SITE


class Votable(models.Model):
    """Abstract class to represent votable objects"""

    class Meta:
        abstract = True

    users_upvoted = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="+")
    users_downvoted = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="+",
    )
    votes = models.IntegerField(default=0)


class UserInput(Editable):
    """Abstract class to represent 'main' user input, i.e., question and answers (but not comment)."""

    class Meta:
        abstract = True

    content = models.TextField()

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="+",
    )

    def get_model(self) -> str:
        raise NotImplementedError

    def get_question(self) -> "Question":
        raise NotImplementedError

    def get_answer(self) -> Optional["Answer"]:
        """Used for `Activity` model.
        For question userinput, returns None
        For answer userinput, returns self.
        :returns: None
        """
        raise NotImplementedError

    def share_link(self) -> str:
        raise NotImplementedError

    @property
    def is_answer(self):
        return self.get_answer() is not None


class VotableUserInput(UserInput, Votable):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.id is not None:
            logger.debug(f"`{self.__class__.__name__}:{self.id}`, updating votes before saving")
            self.votes = self.users_upvoted.count() - self.users_downvoted.count()
        self.content = dedent_code(self.content)
        super(VotableUserInput, self).save(*args, **kwargs)


class QuestionManager(models.Manager):
    def __init__(self):
        super(QuestionManager, self).__init__()
        db_engine = settings.DATABASES["default"]["ENGINE"]
        self.support_postgres_fts = db_engine == "django.db.backends.postgresql"

    def with_documents(self):
        if self.support_postgres_fts:
            vector = (
                SearchVector("title", weight="A")
                + SearchVector("content", weight="B")
                + SearchVector(StringAgg("tags__tag_word", delimiter=","), weight="B")
                + SearchVector(
                    StringAgg("answer__content", delimiter="\n", output_field=TextField()),
                    weight="D",
                )
            )
        else:
            vector = F("title")
        return super(QuestionManager, self).get_queryset().annotate(document=vector)


class Question(VotableUserInput, Flaggable, Followable):
    """Class to represent a post in the forum"""

    class PostType(models.TextChoices):
        ARTICLE = "a", "Article"
        QUESTION = "q", "Question"
        HOWTO = "h", "How to"
        DISCUSSION = "d", "Discussion"

    class PostStatus(models.TextChoices):
        OPEN = "a", "Open"
        TRIAGED = "t", "Triaged"
        CLOSED = "c", "Closed"
        DUPLICATE = "d", "Duplicate"
        HIDDEN = "h", "Hidden"
        OFF_TOPIC = "O", "Off Topic"
        NEEDS_DETAILS = "N", "Needs details or Clarity"

    POST_ARTICLE_TYPES = {PostType.ARTICLE, PostType.HOWTO}
    POST_TYPE_ACCEPTING_ANSWERS = {PostType.QUESTION, PostType.DISCUSSION}
    POST_STATUS_ACCEPTING_ANSWERS = {PostStatus.OPEN, PostStatus.TRIAGED}
    SOURCES = [
        ("slack", "Slack"),
        ("teams", "Microsoft Teams"),
    ]
    status = models.CharField(
        max_length=2,
        choices=PostStatus.choices,
        default=PostStatus.OPEN,
        help_text="Post status",
    )
    status_updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When was the status last updated",
    )
    type = models.CharField(
        max_length=2,
        choices=PostType.choices,
        default=PostType.QUESTION,
        help_text="Post type",
    )
    answers_count = models.IntegerField(
        default=0,
        help_text="Count number of answers",
    )
    views = models.IntegerField(
        default=0,
        help_text="Number of views for post",
    )
    last_activity = models.DateTimeField(
        default=timezone.now,
        help_text="When was last activity created",
    )
    title = models.CharField(
        max_length=255,
        help_text="Post title",
    )
    tags = models.ManyToManyField(
        Tag,
        help_text="Tags post is asscociated with",
    )
    is_anonymous = models.BooleanField(
        default=False,
        help_text="Is post anonymous?",
    )
    has_accepted_answer = models.BooleanField(
        default=False,
        help_text="Does post have an accepted answer?",
    )
    space = models.ForeignKey(
        Space,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Space post is associated with",
    )
    source = models.CharField(
        max_length=10,
        choices=SOURCES,
        null=True,
        blank=True,
        help_text="Post source platform (slack, etc.)",
    )
    source_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="id in the source platform",
    )
    link = models.URLField(
        null=True,
        blank=True,
        help_text="Link to post source in its originating platform",
    )
    objects = QuestionManager()

    def __str__(self):
        return f"[{self.id}] {self.title} ({self.author.display_name()})"

    def post_accepts_answers(self):
        return self.type in Question.POST_TYPE_ACCEPTING_ANSWERS

    def get_author(self) -> settings.AUTH_USER_MODEL:
        return self.author

    @property
    def is_accepting_answers(self):
        return (
            self.type in Question.POST_TYPE_ACCEPTING_ANSWERS and self.status in Question.POST_STATUS_ACCEPTING_ANSWERS
        )

    @property
    def is_article(self):
        return self.type in Question.POST_ARTICLE_TYPES

    @property
    def is_question(self):
        return self.type == Question.PostType.QUESTION

    @property
    def is_discussion(self):
        return self.type == Question.PostType.DISCUSSION

    @property
    def duplicate_question_link(self):
        flags = self.flags.all()
        for flag in flags:
            if flag.flag_type == "duplicate" and flag.extra:
                return flag.extra

    @property
    def is_old(self):
        if config.DAYS_FOR_QUESTION_TO_BECOME_OLD is None:
            return False
        old_question_date = timezone.now() - timedelta(days=config.DAYS_FOR_QUESTION_TO_BECOME_OLD)
        return self.created_at < old_question_date

    def get_question(self):
        return self

    def share_link(self) -> str:
        return f"{CURRENT_SITE}{reverse('forum:thread', args=[self.pk])}#question_{self.pk}"

    def get_model(self) -> str:
        return "question"

    def get_answer(self):
        return None

    def tag_words(self) -> list[str]:
        return [t.tag_word for t in self.tags.all()]

    def save(self, *args, **kwargs):
        super(Question, self).save(*args, **kwargs)
        additional_data, _ = QuestionAdditionalData.objects.get_or_create(question=self)
        additional_data.save()

    def user_can_delete(self, user) -> bool:
        return self.author == user or user.is_staff or user.is_moderator

    def viewed_by(self, user: AbstractUser, pot: datetime) -> bool:
        """Returns whether question was viewed by user since pot
        :param user: user who viewed
        :param pot: check views since
        :returns: Whether user view this question since pot
        """
        return self.questionview_set.filter(author=user, created_at__gte=pot).exists()


class QuestionAdditionalData(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, blank=False)
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = (GinIndex(fields=["search_vector"]),)
        default_related_name = "additional_data"

    def save(self, *args, **kwargs):
        instance = Question.objects.with_documents().get(id=self.question_id)
        self.search_vector = instance.document
        super(QuestionAdditionalData, self).save(*args, **kwargs)


class Answer(VotableUserInput, Flaggable):
    """Class to represent an answer to a question in the forum"""

    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False)
    parent = models.ForeignKey("Answer", on_delete=models.SET_NULL, blank=True, null=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"[Ans{self.id} to Q{self.question_id}] {self.question.title} ({self.author.display_name()})"

    class Meta:
        order_with_respect_to = "question"

    @property
    def is_recent(self):
        recent_answer_date = timezone.now() - timedelta(days=config.ANSWER_IS_RECENT_DAYS)
        return self.created_at >= recent_answer_date

    def get_question(self) -> Question:
        return self.question

    def get_model(self) -> str:
        return "answer"

    def get_author(self) -> settings.AUTH_USER_MODEL:
        return self.author

    def share_link(self) -> str:
        return f"{CURRENT_SITE}{reverse('forum:thread', args=[self.question.pk])}#answer_{self.pk}"

    def get_answer(self) -> Optional["Answer"]:
        return self

    def save(self, *args, **kwargs) -> None:
        if self.id is None:  # New answer, increase counter
            self.question.answers_count += 1
        super(Answer, self).save(*args, **kwargs)
        if self.is_accepted:
            self.question.has_accepted_answer = True
        self.question.last_activity = self.updated_at
        self.question.save()

    def delete(self, using=None, keep_parents=False):
        super(Answer, self).delete()
        self.question.answers_count -= 1
        if self.is_accepted:
            self.question.has_accepted_answer = False
        self.question.last_activity = timezone.now()
        self.question.save()


class QuestionView(models.Model):
    """
    Represent recent Post (thread) view by user.
    Table should be purged frequently.
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        help_text="Who viewed the post",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When was the post viewed",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        blank=False,
        help_text="Post that was viewed (Represented by the question",
    )

    def __str__(self):
        return f"QuestionView[q={self.question_id},u={self.author.username},t={self.created_at.isoformat()}]"

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        if not created:
            return
        instance.question.views += 1
        instance.question.save()
        logger.debug(f"Create {instance.__str__()}")


post_save.connect(QuestionView.post_create, sender=QuestionView)
