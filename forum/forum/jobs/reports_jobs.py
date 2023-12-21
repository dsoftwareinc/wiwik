import datetime

import django.core.mail
from django.utils import timezone
from scheduler import job

from forum.jobs import notify_user
from forum.jobs.base import logger
from forum.reports import (
    recent_questions_email_report,
    generate_report_html,
    tags_activity_email_report,
    user_activity_email_report,
    old_unanswered_questions_email_report,
    tags_author_should_report,
)
from forum.views import utils as viewutils
from userauth.models import ForumUser
from userauth.utils import unsubscribe_link_with_base


def weekly_digest_to_user(
    user: ForumUser,
    fromdate: datetime.datetime,
):
    logger.debug(f"Sending weekly digest to user {user.username}")
    tags = viewutils.get_user_followed_tags(user)
    if len(tags) == 0:
        logger.debug(f"User {user.username} does not follow any tags, skipping sending digest")
        # todo send notification to watch some tags? should be only once.
        return ""
    tag_words = [tag.tag_word for tag in tags]
    tags_empty_desc = tags_author_should_report(user)
    digest_report = recent_questions_email_report(fromdate, tag_words, skip_if_empty=True)
    unanswered_questions = old_unanswered_questions_email_report(tag_words, skip_if_empty=True)
    if digest_report == "":
        logger.debug(f"Report for {user.username} has nothing in it, skipping sending digest")
        return ""
    html = generate_report_html(
        f"Hi {user.display_name()}, here is a weekly digest from wiwik",
        [
            tags_empty_desc,
            digest_report,
            unanswered_questions,
        ],
        unsubscribe_link_with_base(user),
    )
    return html


@job("cron")
def send_weekly_digest_for_users():
    fromdate = timezone.now() - datetime.timedelta(days=7)
    user_qs = ForumUser.objects.filter(is_superuser=False, is_active=True, email_notifications=True)
    logger.debug(f"Sending weekly digest to {len(user_qs)} users")
    subject = f"Weekly digest on tags you are following, activity since {fromdate.date()}"
    for user in user_qs:
        html = weekly_digest_to_user(user, fromdate)
        if not html:
            continue
        notify_user.notify_user_email(user, subject, subject, html, True)


@job("cron")
def send_daily_activity_report_for_admins():
    fromdate = timezone.now() - timezone.timedelta(days=1)
    reports_list = [
        tags_activity_email_report(fromdate),
        user_activity_email_report(fromdate),
        recent_questions_email_report(fromdate),
        old_unanswered_questions_email_report(),
    ]
    subject = f"Daily activity report {fromdate.date()}-{datetime.date.today()}"
    html = generate_report_html(subject, reports_list, None)
    django.core.mail.mail_admins(subject, subject, html_message=html)
