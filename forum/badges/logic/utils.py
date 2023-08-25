import dataclasses
from collections import namedtuple
from typing import Type, Callable

from django.db import models as base_models

from userauth.models import ForumUser

BadgeCalculation = namedtuple('BadgeCalculation', ['deserved', 'needed_for_next'])


@dataclasses.dataclass(frozen=True)
class BadgeData:
    name: str
    description: str
    logic: Callable[[ForumUser, ], BadgeCalculation]
    type: str
    only_once: bool
    trigger: int
    group: int = None
    required: int = None


class BadgeType:
    GOLD = 'gold'
    SILVER = 'silver'
    BRONZE = 'bronze'


TRIGGER_EVENT_TYPES = {
    'Upvote': 0,
    'Accept answer': 1,
    'Update post': 2,
    'Create post': 3,
    'View post': 4,
    'Edit profile': 5,
    'Create comment': 6,
    'Visit': 7,
    'Bookmark thread': 8,
    'Synonym approved': 9,
    'Tag edit': 10,
    'Tag created': 11,
}


def user_authored_vs_required(
        model: Type[base_models.Model],
        required: int,
        user: ForumUser) -> BadgeCalculation:
    """
       Should be used with partial(model, required) so it will return
       a method accepting a user and returning the number of instances
       the user authored divided by required

       Args:
           model: The model to query
           required: the number of rows to divide by
           user: parameter for actual run of method

       Returns:
           A tuple: model count // required, model count % required
   """
    count = model.objects.filter(author=user).count()
    return divmod(count, required)
