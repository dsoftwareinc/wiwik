from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied

from spaces.models import Space


def validate_space_access(space: Space, user: AbstractUser) -> None:
    if not user.is_active:
        raise PermissionDenied()
    access_granted = not space.restricted
    access_granted = access_granted or user.is_staff
    access_granted = access_granted or space.author == user
    access_granted = access_granted or (space.spacemember_set.filter(user=user).count() > 0)
    if not access_granted:
        raise PermissionDenied()
