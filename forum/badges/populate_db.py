from badges.logic import badges
from badges.models import Badge

from .apps import logger

BADGE_LOGIC = dict()


def upsert_badges_in_db() -> None:
    """
    Check that badges exist in the database and update them based on map values.
    This method should run during app loading.

    :returns: None
    """
    for section in badges:
        logger.debug(f'Populating {len(badges[section])} badges for section {section}')
        for badge_data in badges[section]:
            badge, created = Badge.objects.get_or_create(name=badge_data.name)
            if created:
                logger.debug(f'Creating badge {badge_data.name} in DB: {badge_data}')
            badge.description = badge_data.description
            badge.type = badge_data.type
            badge.only_once = badge_data.only_once
            badge.section = section
            badge.trigger = badge_data.trigger
            badge.group = badge_data.group
            if badge.name in BADGE_LOGIC and BADGE_LOGIC[badge.name] != badge_data.logic:
                logger.error(f'Logic for badge {badge.name} changed')
                raise ValueError(f'Logic for badge {badge.name} changed')
            BADGE_LOGIC[badge.name] = badge_data.logic
            badge.save()
