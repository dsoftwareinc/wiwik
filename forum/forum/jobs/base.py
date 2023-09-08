import redis
from django.conf import settings

from forum.apps import logger


def start_job(method, *args, **kwargs):
    """This method starts a job in the background.
    If RUN_ASYNC_JOBS_SYNC flag is on, then it runs it.
    """
    if settings.RUN_ASYNC_JOBS_SYNC:
        logger.debug(f'running job {method.__name__}')
        method(*args, **kwargs)
        return
    try:
        method.delay(*args, **kwargs)
        logger.debug(f'started job {method.__name__}')
    except redis.exceptions.ConnectionError as e:
        logger.warning(f'Could not publish job {method} to redis: {e}')
