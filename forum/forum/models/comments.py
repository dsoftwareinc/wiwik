"""
It does not (and should not) contain logic on these models.
"""

from django.conf import settings
from django.db import models

from wiwik_lib.models import AdvancedModelManager, user_model_defer_fields, Flaggable
from .base import Answer, Question


class Comment(Flaggable):
    """An abstract class to represent a comment to a user input.
    """

    class Meta:
        abstract = True

    # A comment doesn't follow the list of users who up/down voted,
    # only the number of votes.
    votes = models.IntegerField(default=0)
    content = models.TextField(max_length=300)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    users_upvoted = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='+')

    def get_model(self) -> str:
        raise NotImplementedError

    def get_question(self) -> Question:
        raise NotImplementedError

    def __str__(self):
        return f'({self.author}) {self.content}'

    def save(self, *args, **kwargs):
        update_last_activity = self.id is None
        super(Comment, self).save(*args, **kwargs)
        if update_last_activity:
            q = self.get_question()
            q.last_activity = self.created_at
            q.save()


class AnswerComment(Comment):
    """A class representing a comment to an answer.
    """
    objects = AdvancedModelManager(select_related=('author',), deferred_fields=user_model_defer_fields('author'))

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Answer Comment'
        verbose_name_plural = 'Answer Comments'

    answer = models.ForeignKey(Answer,
                               on_delete=models.CASCADE,
                               blank=False,
                               related_name='comments', )

    def get_model(self):
        return 'comment_answer'

    def get_question(self) -> Question:
        return self.answer.get_question()


class QuestionComment(Comment):
    """A class representing a comment to a question.
    """
    objects = AdvancedModelManager(select_related=('author',), deferred_fields=user_model_defer_fields('author'))

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Question Comment'
        verbose_name_plural = 'Question Comments'

    question = models.ForeignKey(Question, on_delete=models.CASCADE, blank=False, related_name='comments', )

    def get_model(self):
        return 'comment_question'

    def get_question(self):
        return self.question
