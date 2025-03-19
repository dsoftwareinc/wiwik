"""
This file handles notifying followers about changes in
questions/tags they are following.
"""
import shlex
from typing import Set, List

from constance import config
from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from django.template import loader

from forum import models, jobs
from forum.apps import logger
from forum.integrations import slack_api
from forum.views.common import get_model_url_with_base
from userauth.models import ForumUser
from userauth.utils import unsubscribe_link_with_base
from wiwik_lib.utils import CURRENT_SITE


def _get_user_display_name(user: AbstractUser) -> str:
    return user.display_name() if isinstance(user, ForumUser) else user.username


def notify_slack_channel(msg: str, channel: str) -> None:
    if channel is None:
        return
    logger.debug(f"Sending slack channel {channel} msg: {msg}")
    jobs.start_job(slack_api.slack_post_channel_message, msg, channel)


def _notify_question_followers(
    originator: AbstractUser,
    question: models.Question,
    subject: str,
    activity: str,
    html: str,
    important: bool,
) -> list[ForumUser]:
    follows = question.follows.filter(~Q(user=originator), user__is_active=True)
    users = [follow.user for follow in follows]
    logger.debug(
        f"Notifying {len(follows)} followers of question {question.id} "
        f"activity by {originator.username}, len: {len(activity)}"
    )
    for follow in follows:
        jobs.start_job(jobs.notify_user_email, follow.user, subject, activity, html, important)
    return users


def notify_tag_followers_new_question(originator: AbstractUser, tag_words: Set[str], q: models.Question) -> None:
    """
    1. Notify in slack channel about a new question
    2. Notify tag followers about a new question

    Args:
        originator: Question author
        tag_words: Tags list
        q: The question

    Returns:
        None
    """
    slack_template = loader.get_template("slack/new_question.md")
    slack_msg = slack_template.render(context={"q": q, "basesite": CURRENT_SITE, "tags": ", ".join(q.tag_words())})
    notify_slack_channel(slack_msg, config.SLACK_NOTIFICATIONS_CHANNEL)
    emails_dict = dict()
    for tag_word in tag_words:
        follows = list(
            models.UserTagStats.objects.filter(~Q(user=originator), user__is_active=True, tag__tag_word=tag_word)
        )
        for follow in follows:
            emails_dict[follow.user] = tag_word
    model_url = get_model_url_with_base(q.get_model(), q)
    context = {
        "link": model_url,
        "username": originator,
        "basesite": CURRENT_SITE,
        "q": q,
        # tag_word key should be inserted later
    }
    activity_str = f"New question on tag: {q.title}\n" + f"link: {model_url} Question content:\n{q.content}"
    template = loader.get_template("emails/new_question.html")
    logger.debug(f"Notifying {len(emails_dict)} followers about activity: {activity_str}")
    for user in emails_dict:
        html = template.render(context={"tag_word": emails_dict[user], **context})
        jobs.start_job(
            jobs.notify_user_email,
            user,
            f"Activity in tag {emails_dict[user]}",
            activity_str,
            html,
            False,
        )


def notify_question_changes(
    originator: AbstractUser,
    q: models.Question,
    old_title: str,
    old_content: str,
):
    if originator == q.author:
        logger.debug("Question author edited, skipping notification.")
        return
    if old_content == q.content and old_title == q.title:
        return
    model_url = get_model_url_with_base(q.get_model(), q)
    context = {
        "link": model_url,
        "old_title": old_title,
        "old_content": old_content,
        "basesite": CURRENT_SITE,
        "q": q,
    }
    user_display_name = _get_user_display_name(originator)
    activity_str = (
        f'Question "{q.title}" by {q.author.username} ' f"was updated by {user_display_name}\n" f"link: {model_url}\n"
    )
    if old_title != q.title:
        activity_str += f'Title changed from "{old_title}" to "{q.title}"\n'
    if old_content != q.content:
        activity_str += f"Content changed from:\n\n {old_content} \n\nto:\n\n {q.content}\n"
    subject = f"A question you are following was edited by {user_display_name}"
    template = loader.get_template("emails/question_updated.html")
    html = template.render(context=context)
    jobs.start_job(jobs.notify_user_email, q.author, subject, activity_str, html, False)


def notify_new_answer(originator: AbstractUser, a: models.Answer):
    model_url = get_model_url_with_base(a.get_model(), a)
    context = {
        "link": model_url,
        "basesite": CURRENT_SITE,
        "a": a,
    }
    user_display_name = _get_user_display_name(originator)
    activity_str = f'New answer to "{a.question.title}" by {user_display_name} was added\n' + f"link: {model_url}\n"
    subject = f"New answer by {user_display_name} on a question you are following"
    template = loader.get_template("emails/new_answer.html")
    html = template.render(context=context)
    _notify_question_followers(originator, a.get_question(), subject, activity_str, html, True)
    jobs.start_job(slack_api.slack_post_im_message_to_email, activity_str, a.question.author.email)


def notify_answer_changes(originator: AbstractUser, a: models.Answer, old_content: str):
    if originator == a.author:
        logger.debug("Answer author edited, skipping notification.")
        return
    # Build html
    user_display_name = _get_user_display_name(originator)
    q = a.get_question()
    model_url = get_model_url_with_base(a.get_model(), a)
    context = {
        "link": model_url,
        "old_content": old_content,
        "a": a,
        "basesite": CURRENT_SITE,
        "unsubscribe_link": unsubscribe_link_with_base(a.author),
    }
    activity_str = f'Answer to "{q.title}" by {a.author} was updated' + f"link: {model_url}\n"
    subject = f"Your answer to a question was edited by {user_display_name}"
    template = loader.get_template("emails/answer_updated.html")
    html = template.render(context=context)
    jobs.start_job(jobs.notify_user_email, a.author, subject, activity_str, html, False)
    jobs.start_job(slack_api.slack_post_im_message_to_email, activity_str, a.author.email)


def notify_new_comment(
    originator: AbstractUser,
    parent: models.VotableUserInput,
    comment: models.Comment,
) -> None:
    link_url = get_model_url_with_base(parent.get_model(), parent)
    context = {
        "link": link_url,
        "q": parent.get_question(),
        "user": originator,
        "content": comment.content,
        "basesite": CURRENT_SITE,
    }
    user_display_name = _get_user_display_name(originator)
    activity_str = (
        f'New comment to "{parent.get_question().title}" {parent.get_model()} '
        f"by {user_display_name} was added\n"
        f"link: {link_url}\n"
    )
    template = loader.get_template("emails/new_comment.html")
    html = template.render(context=context)
    if parent.get_model() == "question":
        subject = f"New comment by {user_display_name} on a question you are following"
        notified_users = _notify_question_followers(
            originator, parent.get_question(), subject, activity_str, html, True
        )
    else:
        subject = f"New comment by {user_display_name} on your answer"
        jobs.start_job(jobs.notify_user_email, parent.author, subject, activity_str, html, False)
        notified_users = [
            parent.author,
        ]
    jobs.start_job(slack_api.slack_post_im_message_to_email, activity_str, parent.author.email)
    # Handling mentions
    if "@" not in comment.content:
        return
    mentioned_users = list()
    try:
        parts = shlex.split(comment.content)
    except ValueError:
        parts = shlex.split(comment.content.replace('"', "'") + "'")
    for part in parts:
        if part.startswith("@"):
            username = part[1:]
            u = ForumUser.objects.filter(username=username).first()
            if u is None or (u in notified_users):
                continue
            mentioned_users.append(u)
    if len(mentioned_users) == 0:
        return
    logger.debug(f"Informing users they were mentioned: {mentioned_users}")
    template = loader.get_template("emails/user_mentioned.html")
    html = template.render(context=context)
    subject = f"{user_display_name} mentioned you in a comment"
    for user in mentioned_users:
        jobs.start_job(jobs.notify_user_email, user, subject, activity_str, html, False)


def notify_invite_users_to_question(
    inviter: AbstractUser,
    question: models.Question,
    invited_list: List[AbstractUser],
) -> None:
    if len(invited_list) == 0:
        return None
    subject = f"{inviter.username} invited you to answer a question"
    model_url = get_model_url_with_base(question.get_model(), question)
    text = f"{inviter.username} invited you to answer the question: {question.title}\n" f"link: {model_url}"
    # Build html to send
    context = {
        "inviter": inviter,
        "q": question,
        "basesite": CURRENT_SITE,
    }
    template = loader.get_template("emails/invite_to_answer_question.html")
    html = template.render(context=context)
    for invitee in invited_list:
        jobs.start_job(jobs.notify_user_email, invitee, subject, text, html, True)
        jobs.start_job(slack_api.slack_post_im_message_to_email, text, invitee.email)
