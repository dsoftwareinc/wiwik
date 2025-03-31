import os
from datetime import datetime, timedelta
from typing import Union

import geoip2.database
from django.conf import settings
from geoip2.errors import AddressNotFoundError
from scheduler import job

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from forum import jobs
from userauth.apps import logger
from userauth.models import ForumUser, UserVisit

reader = geoip2.database.Reader(os.path.join(settings.BASE_DIR, "GeoLite2-City.mmdb"))
MAX_MS_TIME_FOR_REQUEST = 400


@job(
    "default",
    result_ttl=5,
)
def log_request(
    user_id: int, client_ip: str, time: Union[str, datetime], duration: int, method: str, path: str
) -> None:
    log_method = logger.warning if duration > MAX_MS_TIME_FOR_REQUEST else logger.debug
    user = ForumUser.objects.get(id=user_id)
    log_method(f'{user.username},"{method} {path}" took {duration}ms')
    try:
        location = reader.city(client_ip)
        country_name = location.country.name
        city_name = location.city.name
    except AddressNotFoundError:
        country_name = None
        city_name = None

    if isinstance(time, str):
        time = datetime.fromisoformat(time)
    if UserVisit.objects.filter(user=user, visit_date=time.date(), country=country_name, city=city_name).exists():
        return
    consecutive_days = (
        UserVisit.objects.filter(user=user, visit_date=time.date() - timedelta(days=1))
        .order_by("-visit_date")
        .values_list("consecutive_days", flat=True)
        .first()
        or 0
    ) + 1
    total_days = (
        UserVisit.objects.filter(user=user).order_by("-total_days").values_list("total_days", flat=True).first() or 0
    ) + 1
    max_consecutive_days = max(
        UserVisit.objects.filter(user=user)
        .order_by("-consecutive_days")
        .values_list("consecutive_days", flat=True)
        .first()
        or 0,
        consecutive_days,
    )
    UserVisit.objects.create(
        user=user,
        ip_addr=client_ip,
        visit_date=time.date(),
        country=country_name,
        city=city_name,
        consecutive_days=consecutive_days,
        max_consecutive_days=max_consecutive_days,
        total_days=total_days,
    )
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Visit"])
