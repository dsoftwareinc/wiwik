from django.db import models

from badges.logic.utils import TRIGGER_EVENT_TYPES, BadgeType

TRIGGER_EVENT_TYPES_LIST = [(TRIGGER_EVENT_TYPES[k], k) for k in TRIGGER_EVENT_TYPES]


class Badge(models.Model):
    BADGE_TYPES = [
        (BadgeType.GOLD, 'Gold'),
        (BadgeType.SILVER, 'Silver'),
        (BadgeType.BRONZE, 'Bronze'),
    ]
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(
        max_length=30,
        help_text='Short name of badge',
        unique=True,
    )
    group = models.IntegerField(
        default=None, null=True, blank=True,
        help_text='For grouping badges with increasing criteria',
    )
    section = models.CharField(
        max_length=30,
        help_text='Section of this badge',
    )
    description = models.CharField(
        max_length=300,
        help_text='Description how a user can get this badge',
    )
    type = models.CharField(
        max_length=10,
        choices=BADGE_TYPES,
        help_text='Badge type',
    )
    active = models.BooleanField(default=True)
    only_once = models.BooleanField(
        default=True,
        help_text='Can this badge be earned only once or more than once'
    )
    trigger = models.IntegerField(
        null=True, blank=True, default=None,
        choices=TRIGGER_EVENT_TYPES_LIST,
    )

    def __str__(self):
        return f'{self.name}'

    @property
    def count(self):
        return self.voteactivity_set.count()
