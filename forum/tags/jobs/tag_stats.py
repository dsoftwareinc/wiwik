from scheduler import job

from tags import utils
from tags.apps import logger
from tags.models import Tag


@job
def update_tag_stats():
    logger.info('Updating all tag stats')
    for tag in Tag.objects.all():
        utils.update_tag_stats_for_tag(tag)
