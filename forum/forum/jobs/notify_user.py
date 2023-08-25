"""
This file handles notifying a user in email.
"""
from datetime import timedelta

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils import timezone
from scheduler import job

from forum.jobs.base import logger
from userauth.models import ForumUser
from userauth.utils import unsubscribe_link_with_base


def send_email_async(email: EmailMessage) -> None:
    """
    Sending an email message.
    If in DEBUG mode ensures that email is not sent to the real user.

    Args:
        email: EmailMessage to be sent.

    Returns:
        None
    """
    if not settings.SEND_EMAILS:  # preventing sending emails to others when on DEBUG mode
        email.to = [settings.DEBUG_EMAIL_TO, ]
    logger.debug(f'Sending email to {email.to} with subject {email.subject}')
    email.send()


def should_notification_be_skipped(user: ForumUser, important: bool, ) -> bool:
    """
    Returns whether a user notification should be skipped.
    A notification should be skipped if it is not important and the user recently
    received another notification.
    Also, it checks whether settings.ALLOW_USER_NOTIFICATION_SKIPPING is enabled.

    Args:
        user: The user to notify
        important: is the notification important?

    Returns:
        True: if the notification should be skipped
        False: otherwise

    """
    if not settings.ALLOW_USER_NOTIFICATION_SKIPPING:
        return False
    if not user.email_notifications:
        logger.debug(f'{user.email} does not have email notifications enabled')
        return True
    max_acceptable_time = timezone.now() - timedelta(hours=1)
    if (not important
            and user.last_email_datetime is not None
            and user.last_email_datetime > max_acceptable_time):
        logger.debug(f'{user.email} received another notification recently')
        return True
    return False


def fix_subject(subject: str) -> str:
    """
    Adding [wiwik] prefix to all email subjects sent.
    Add only if it is not there.

    Args:
        subject: original subject

    Returns:
        subject with [wiwik] prefix

    """
    if not subject.startswith('[wiwik]'):
        subject = f'[wiwik] {subject}'
    return subject


def fix_html(html: str, user: ForumUser) -> str:
    """
    Adding unsubscribe link if needed to html.

    Args:
        html: html text
        user: user to build unsubscribe link

    Returns:
        html with guarenteed unsubscribe link
    """
    soup = BeautifulSoup(html, 'html.parser')
    no_unsubscribe_link = (len(soup.find_all('a', {'id': 'unsubscribe_link'})) == 0)
    if no_unsubscribe_link:
        unsubscribe_url = unsubscribe_link_with_base(user)
        unsubscribe_template = loader.get_template('emails/unsubscribe.html')
        unsubscribe_html = unsubscribe_template.render(context={
            'user': user,
            'unsubscribe_link': unsubscribe_url,
        })
        html += unsubscribe_html
    return html


@job
def notify_user_email(user: ForumUser, subject: str, text: str, html: str, important: bool = False):
    if not user.is_active:
        logger.debug(f'skipping notification to {user.email}: user inactive')
        return
    if should_notification_be_skipped(user, important):
        logger.debug(f'skipping notification to {user.email}: subject: {subject}, text-length: {len(text)}')
        return
    subject = fix_subject(subject)
    logger.debug(f'Notifying {user.email}, subject: {subject}, '
                 f'text-length: {len(text)}, '
                 f'html-length: {len(html) if html else 0}')
    email = EmailMultiAlternatives(subject, text, to=[user.email])
    if html is not None:
        html = fix_html(html, user)
        email.attach_alternative(html, "text/html")
    send_email_async(email)
    # Update user last email
    user.last_email_datetime = timezone.now()
    user.save()
