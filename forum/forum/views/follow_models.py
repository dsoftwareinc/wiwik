from django.contrib.auth.models import AbstractUser

from forum import models
from forum.apps import logger
from tags.models import Tag


def create_follow_tag(tag: Tag, user: AbstractUser) -> models.UserTagStats:
    tag_follow = models.UserTagStats.objects.filter(tag=tag, user=user).first()
    if tag_follow is not None:
        logger.debug(f'user {user.username} trying to follow tag {tag.tag_word} which they already follow')
        return tag_follow
    logger.debug(f'Adding {user.username} to tag {tag.tag_word} followers')
    tag_follow = models.UserTagStats.objects.create(tag=tag, user=user)
    return tag_follow


def delete_follow_tag(tag: Tag, user: AbstractUser):
    follow = models.UserTagStats.objects.filter(tag=tag, user=user).first()
    if follow is None:
        logger.debug(f'user {user.username} trying to unfollow tag {tag.tag_word} which they do not follow')
        return
    logger.debug(f'Removing {user.username} from tag {tag.tag_word} followers')
    follow.delete()
