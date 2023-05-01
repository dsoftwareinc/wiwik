from django.conf import settings
from django.db import models

from userauth.models import ForumUser
from wiwik_lib.models import Flaggable, Editable


class Tag(Flaggable, Editable):
    """
    Class to represent a tag.
    A question can be tagged with multiple tags.
    User can follow tags.
    """
    tag_word = models.CharField(max_length=25, unique=True)
    description = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    wiki = models.TextField(default='', blank=True, )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, )
    number_of_questions = models.IntegerField(
        default=0, help_text='total number of questions with this tag asked', )
    number_asked_today = models.IntegerField(
        default=0, help_text='number of questions with this tag asked today', )
    number_asked_this_week = models.IntegerField(
        default=0, help_text='number of questions with this tag asked this week', )
    number_followers = models.IntegerField(
        default=0, help_text='Number of followers for tag, calculated async', )
    experts = models.CharField(
        max_length=100, default='', blank=True, null=True,
        help_text='Comma separated list of usernames that are considered experts',
    )
    stars = models.CharField(
        max_length=100, default='', blank=True, null=True,
        help_text='Comma separated list of usernames that are considered stars',
    )
    related = models.CharField(
        max_length=100, default='', blank=True, null=True,
        help_text='Comma separated list of related tags',
    )

    def __str__(self):
        return (f'Tag[{self.tag_word};'
                f'#Qs={self.number_of_questions};#Qs/week={self.number_asked_this_week};'
                f'#Qs/day={self.number_asked_today};#followers={self.number_followers};'
                f'related={self.related};'
                f'experts={self.experts};stars={self.stars};]')

    def experts_list(self):
        usernames_list = self.experts.split(',') if self.experts else []
        return list(ForumUser.objects.filter(username__in=usernames_list))

    def stars_list(self):
        usernames_list = self.stars.split(',') if self.stars else []
        return list(ForumUser.objects.filter(username__in=usernames_list))

    def related_tags(self):
        return self.related.split(',') if self.related else None


class TagEdit(models.Model):
    """
    Class represents an edit made by a user on a tag wiki.
    """
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, )
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL,
                               blank=True, null=True,
                               )
    summary = models.CharField(max_length=200)
    before_wiki = models.TextField(null=True, blank=True)
    before_description = models.TextField(null=True, blank=True)

    def __str__(self):
        return (f'TagEdit['
                f'tag={self.tag.tag_word},'
                f'summary={self.summary},'
                f'created_at={self.created_at}]')


class Synonym(models.Model):
    """
    class represents a synonym for a tag.
    a different name for a tag, for example angular-routes and ng-routes.
    """
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    name = models.CharField(max_length=25, unique=True)
    active = models.BooleanField(default=False, help_text='Is synonym active in searching for tags')
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+')

    def __str__(self):
        return f'Synonym[{self.name} tag_word={self.tag.tag_word} at={self.created_at}]'
