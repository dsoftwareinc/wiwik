import logging
import time

import redis
from django.conf import settings
from django.utils import timezone
from ipware import get_client_ip

from userauth.jobs import log_request

logger = logging.getLogger(__name__)


class UserVisitMiddleware:
    """
    This middleware analyze each request going through django.
    It calculates the time the request took and sends the data to be
    analyzed and logged asynchronously.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if settings.SKIP_USER_VISIT_LOG:
            return self.get_response(request)
        start_time = time.time()
        response = self.get_response(request)
        duration = int((time.time() - start_time) * 1000)

        if hasattr(request, 'user') and request.user.is_authenticated:
            client_ip, is_routable = get_client_ip(request)
            try:
                log_request.delay(request.user.id, client_ip,
                                  timezone.now(), duration,
                                  request.method, request.path,
                                  )
            except redis.exceptions.ConnectionError as e:  # noqa: F841
                logger.warning('Could not publish log_request job to redis')

        response["X-Page-Generation-Duration-ms"] = duration

        return response
