from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponse
from django.utils import timezone

from wiwik_lib.apps import logger
from wiwik_lib.models import EditedResource, Editable


@login_required
def view_update_edit_resource(request, model_name: str, model_pk: str):
    if request.method != "GET" or model_name not in {'tag', 'question', 'answer'}:
        logger.warning("Weird request.. probably not through the app")
        return HttpResponseBadRequest()
    item = EditedResource.objects.filter(
        user=request.user,
        content_type=ContentType.objects.filter(model=model_name).first(),
        object_id=model_pk).first()
    if item is None:
        return HttpResponseNotFound()
    item.last_ping_at = timezone.now()
    item.save()
    return HttpResponse()


def ask_to_edit_resource(user: AbstractUser, resource: Editable) -> bool:
    """Ask for a user to edit a resource by a user.
    :param user: user asking to edit resource.
    :param resource: resource to be edited.

    :returns: if user can edit the resource (it is not edited by another user in the past 5 minutes)
    """
    # Purge stale data in table

    EditedResource.objects.filter(
        content_type=ContentType.objects.get_for_model(resource),
        object_id=resource.id,
        last_ping_at__lt=timezone.now() - settings.EDIT_LOCK_TIMEOUT).delete()

    first = (EditedResource.objects
             .filter(content_type=ContentType.objects.get_for_model(resource),
                     object_id=resource.id, )
             .order_by('-last_ping_at')
             .first())
    if first is None:
        EditedResource.objects.create(user=user, content_object=resource)
        return True

    return first.user == user


def finish_edit_resource(resource: Editable):
    EditedResource.objects.filter(
        content_type=ContentType.objects.get_for_model(resource),
        object_id=resource.id, ).delete()
