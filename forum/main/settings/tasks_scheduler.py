import os

from scheduler.settings_types import QueueConfiguration, SchedulerConfiguration

SCHEDULER_CONFIG: SchedulerConfiguration = SchedulerConfiguration()

SCHEDULER_QUEUES: dict[str, QueueConfiguration] = {
    "default": QueueConfiguration(
        HOST=os.getenv("REDIS_HOST", "localhost"),
        PORT=int(os.getenv("REDIS_PORT", 6379)),
        DB=int(os.getenv("REDIS_DB", 0)),
        PASSWORD=os.getenv("REDIS_PASSWORD", ""),
    ),
    "cron": QueueConfiguration(
        HOST=os.getenv("REDIS_HOST", "localhost"),
        PORT=int(os.getenv("REDIS_PORT", 6379)),
        DB=int(os.getenv("REDIS_DB", 0)),
        PASSWORD=os.getenv("REDIS_PASSWORD", ""),
    ),
}
