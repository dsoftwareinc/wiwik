from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.db.models import Model
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.template import loader

from forum import jobs
from forum.integrations import slack_api
from forum.views import utils
from forum.views.common import get_model_url, get_model_url_with_base
from userauth.models import ForumUser
from wiwik_lib.apps import logger
from wiwik_lib.models import Flag, FLAG_CHOICES, Flaggable
from wiwik_lib.utils import CURRENT_SITE


def notify_moderators_new_flag(
        originator: ForumUser,
        model,
        model_name: str,
) -> None:
    """
    Send a notification to moderators about new flag.
    Args:
        originator: Who created the flag
        model: the model that was flagged (Question, Answer, QuestionComment, AnswerComment)
        model_name: question, answer, question_comment, answer_comment, tag

    Returns:
        None

    """
    subject = f'New content flagged by {originator.display_name()} on a {model_name.split("_")[0]}'
    model_url = get_model_url_with_base(model_name, model)
    context = {
        'link': model_url,
        'username': originator,
        'content': model.content,
        'model_name': model_name,
        'basesite': CURRENT_SITE,
    }
    template = loader.get_template('emails/new_flag.html')
    html = template.render(context=context)
    activity_str = (f'New content flagged by by {context["username"]}\n'
                    + f"link: {context['link']}")
    moderators = ForumUser.objects.filter(is_moderator=True, is_active=True)
    for moderator in moderators:
        jobs.start_job(jobs.notify_user_email, moderator, subject, activity_str, html, True)
        jobs.start_job(slack_api.slack_post_im_message_to_email, activity_str, moderator.email)


def flag_model(user: AbstractUser, target: Flaggable, flag_type: str, extra: str = None) -> Flag:
    content_type = ContentType.objects.get_for_model(target)
    logger.debug(f'User {user.username} flagging {content_type}:{target.id} of as {flag_type}')
    flag = Flag.objects.create(
        user=user, flag_type=flag_type, extra=extra,
        content_type=content_type, object_id=target.id,
        content_author=target.author)
    return flag


@login_required
def view_flag_model(request, model_pk: int):
    if request.method != "POST":
        logger.info("Some some is trying to make a request not through the app")
        return HttpResponseBadRequest()
    user = request.user
    model_name = request.POST.dict()['model-name']
    model_name_for_user = model_name.split('_')[0]
    instance = utils.get_model(model_name, model_pk)
    if instance is None:
        logger.warning(f'user {user.username} tries to flag {model_name}:{model_pk} which does not exist.')
        return HttpResponseBadRequest()

    flag_type = request.POST.get('flag_type', None)
    if flag_type not in map(lambda x: x[0], FLAG_CHOICES):
        logger.warning(f'user {user.username} tries to flag with a flag type {flag_type} which is invalid')
        return redirect(get_model_url(model_name, instance))
    link = request.POST.get('link', None)
    extra = request.POST.get('extra', None)
    if instance.author == request.user:
        logger.warning(f'user {user.username} tries to flag their own {model_name}.')
        messages.warning(request, f'You cannot flag your own {model_name_for_user}.')
        return redirect(get_model_url(model_name, instance))

    if instance.flags.filter(user=user).count() > 0:
        logger.debug(f'User {user.username} already flagged')
        messages.warning(request, f'You already flagged this {model_name_for_user}.')
        return redirect(get_model_url(model_name, instance))

    flag_model(user, instance, flag_type, link if flag_type == 'duplicate' else extra)
    notify_moderators_new_flag(user, instance, model_name)
    logger.debug(f"Flagging succeeded {user.username}:{model_name}:{model_pk}")
    messages.success(request, f'Successfully flagged this {model_name_for_user}.')

    return redirect(get_model_url(model_name, instance))
