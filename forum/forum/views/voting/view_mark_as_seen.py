from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.utils import timezone

from forum import models
from forum.apps import logger


@login_required
def view_mark_as_seen(request, vote_activity_pk: int):
    user = request.user
    activity = models.VoteActivity.objects.filter(pk=vote_activity_pk).first()
    if activity is None:
        logger.warning(f"Activity with pk={vote_activity_pk} does not exist")
        return HttpResponseNotFound()
    if activity.target != user:
        logger.warning(
            f"user {user.username} is trying to mark activity {activity.id} " f"as seen but they are not the target"
        )
        return HttpResponseForbidden()
    activity.seen = timezone.now()
    activity.save()
    return HttpResponse()


@login_required
def view_all_mark_as_seen(request):
    user = request.user
    models.VoteActivity.objects.filter(target=user).update(seen=timezone.now())
    return HttpResponse()
