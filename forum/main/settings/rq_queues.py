import os

SCHEDULER_QUEUES = {
    'default': {
        # A queue for jobs generated due to user activity (background stats updates,
        # sending notifications, etc.)
        'HOST': os.getenv('REDIS_HOST', 'localhost'),
        'PORT': int(os.getenv('REDIS_PORT', 6379)),
        'DB': int(os.getenv('REDIS_DB', 0)),
        'PASSWORD': os.getenv('REDIS_PASSWORD', ''),
        'DEFAULT_TIMEOUT': 360,
        'DEFAULT_RESULT_TTL': 86400,
    },
    'cron': {
        # a queue for processing scheduled tasks such as weekly digests,
        # checking moderator statuses, etc.
        'HOST': os.getenv('REDIS_HOST', 'localhost'),
        'PORT': int(os.getenv('REDIS_PORT', 6379)),
        'DB': int(os.getenv('REDIS_DB', 0)),
        'PASSWORD': os.getenv('REDIS_PASSWORD', ''),
        'DEFAULT_TIMEOUT': 1800,  # 30 minutes timeout for these jobs
        'DEFAULT_RESULT_TTL': 86400 * 7,  # results live for a week after
    },
}
