from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation, GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AdvancedModelManager(models.Manager):
    def __init__(self, *args, **kwargs):
        self._select_related = kwargs.pop('select_related', None)
        self._prefetch_related = kwargs.pop('prefetch_related', None)
        self._deferred_fields = kwargs.pop('deferred_fields', None)

        super(AdvancedModelManager, self).__init__(*args, **kwargs)

    def get_queryset(self, *args, **kwargs):
        qs = super(AdvancedModelManager, self).get_queryset(*args, **kwargs)

        if self._select_related:
            qs = qs.select_related(*self._select_related)
        if self._prefetch_related:
            qs = qs.prefetch_related(*self._prefetch_related)
        if self._deferred_fields:
            qs = qs.defer(*self._deferred_fields)

        return qs


_BASE_USER_DEFER_LIST = [
    'about_me',
    'github_handle',
    'password',
    'last_login',
    'first_name',
    'last_name',
    'title',
    'slack_userid',
    'next_badge',
    'keybase_user',
    'date_joined',
    'is_staff',
    'is_moderator',
    'email_notifications',
    'search_count',
    'bookmarks_count',
    'last_email_datetime',
    'votes',
    'posts_edited',
    'people_reached', ]


def user_model_defer_fields(user_fieldname: str) -> list[str]:
    return [f'{user_fieldname}__{field}' for field in _BASE_USER_DEFER_LIST]


FLAG_CHOICES = [
    ('rude', 'Rude'),
    ('spam', 'Spam'),
    ('moderator', 'Requires intervention'),
    ('close', 'Should be closed'),
    ('duplicate', 'Duplicate'),
]


class Flag(models.Model):
    """
    A class to represent a flag to a model object (Question, Answer, or Comment).
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=False, related_name='flags_by_user')
    flag_type = models.CharField(max_length=10, choices=FLAG_CHOICES, )
    extra = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    content_author = models.ForeignKey(settings.AUTH_USER_MODEL,
                                       on_delete=models.SET_NULL,
                                       blank=True, null=True,
                                       related_name='flags_for_user', )

    def __str__(self):
        return f'Flag[{self.user.username}, {self.flag_type}: {self.content_type}:{self.object_id}]'


class Flaggable(models.Model):
    """
    An abstract class to represent a flagable object.
    """

    class Meta:
        abstract = True

    flags = GenericRelation(Flag)


class EditedResource(models.Model):
    """
    A class to represent an object that is currently being edited.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        blank=False, related_name='user_editing')

    created_at = models.DateTimeField(auto_now_add=True)
    last_ping_at = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return (f'EditedResource[{self.content_type}:{self.object_id}, '
                f'user={self.user.username}, last_ping_at={self.last_ping_at}]')


class Editable(models.Model):
    """
    An abstract class to represent an editable object.
    """

    class Meta:
        abstract = True

    current_editors = GenericRelation(EditedResource)

    def is_edited(self) -> bool:
        return self.current_editors.exists()


class Follow(models.Model):
    """A class to represent a follow to a model object (Post/Tag)."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             blank=False, related_name='followers')

    created_at = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'Follow[{self.user.username}:{self.content_type}:{self.object_id}]'


class Followable(models.Model):
    """An abstract class to represent a followable object."""

    class Meta:
        abstract = True

    follows = GenericRelation(Follow)
