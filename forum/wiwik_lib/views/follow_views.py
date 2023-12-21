from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType

from wiwik_lib.apps import logger
from wiwik_lib.models import Followable, Follow


def create_follow(obj: Followable, user: AbstractUser) -> None:
    content_type = ContentType.objects.get_for_model(obj)
    if (
        Follow.objects.filter(
            content_type=content_type, object_id=obj.id, user=user
        ).count()
        > 0
    ):
        logger.debug(
            f"user {user.username} trying to follow {content_type}:{obj.id} which they already follow"
        )
        return
    logger.debug(f"Adding {user.username} to {content_type}:{obj.id} followers")
    Follow.objects.create(user=user, content_object=obj)


def delete_follow(obj: Followable, user: AbstractUser) -> None:
    content_type = ContentType.objects.get_for_model(obj)
    logger.debug(f"Deleting follower for {content_type}:{obj.id}")
    Follow.objects.filter(
        content_type=content_type, object_id=obj.id, user=user
    ).delete()
