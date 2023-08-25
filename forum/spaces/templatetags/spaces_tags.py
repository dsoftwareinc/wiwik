from django import template
from django.contrib.auth.models import AbstractUser

from forum.models import Question
from spaces.models import Space

register = template.Library()


@register.filter()
def questions_count(space: Space) -> int:
    return Question.objects.filter(space=space).count()


@register.filter()
def ismember(space: Space, user: AbstractUser) -> bool:
    return space.spacemember_set.filter(user=user).count() > 0
