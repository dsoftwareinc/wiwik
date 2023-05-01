from datetime import date

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils import timezone


class SpaceProperty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL,
                               blank=True, null=True,
                               )
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True, )

    class Meta:
        verbose_name_plural = 'Space properties'

    def __str__(self):
        return f'SpaceProperty[{self.name}, user={self.author}]'

    @property
    def spaces(self):
        return Space.objects.filter(space_property_rel__property=self)


class Space(models.Model):
    short_name = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, )
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, )
    page = models.TextField(
        default='', blank=True, )
    start_date = models.DateField(
        blank=True, null=True, )
    end_date = models.DateField(
        blank=True, null=True, )
    logo = models.ImageField(
        upload_to='space_pics',
        default='space_pics/default_logo.jpg',
        blank=True,
        null=True)
    restricted = models.BooleanField(default=False)

    @property
    def url(self):
        return reverse('spaces:questions', args=[self.id])

    def __str__(self):
        username = self.author.username if self.author else '-'
        return f'Space[name={self.name}, author={username}]'

    @admin.display(ordering='active', boolean=True, )
    def space_active(self):
        now = timezone.now().date()
        start_date = self.start_date or date.min
        end_date = self.end_date or date.max
        return start_date <= now <= end_date

    def member_add(self, user: AbstractUser):
        return SpaceMember.objects.get_or_create(space=self, user=user)

    def member_remove(self, user: AbstractUser):
        membership = self.spacemember_set.filter(user=user).first()
        if membership is not None:
            membership.delete()

    def get_absolute_url(self):
        return reverse('spaces:detail', args=[self.pk, ])

    @property
    def properties(self):
        return SpaceProperty.objects.filter(space_property_rel__space=self).order_by('name')


class SpaceToProperty(models.Model):
    space = models.ForeignKey(
        Space, on_delete=models.CASCADE, related_name='space_property_rel')
    property = models.ForeignKey(
        SpaceProperty, on_delete=models.CASCADE, related_name='space_property_rel')

    def __str__(self):
        return f'SpaceToProperty[space={self.space.short_name},prop={self.property.name}]'


class SpaceMember(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, )
    space = models.ForeignKey(Space, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f'SpaceMember[user={self.user.username}, space={self.space.name}]'

    class Meta:
        unique_together = ('user', 'space',)
