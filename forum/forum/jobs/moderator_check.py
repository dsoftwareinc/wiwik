import datetime

from django.conf import settings
from django.db.models import Count, Q
from django.template import loader
from scheduler import job

from forum.jobs.base import logger
from forum.reports import recent_questions_email_report, generate_report_html
from forum.views import utils as viewutils
from userauth.models import ForumUser
from userauth.utils import unsubscribe_link_with_base
from . import notify_user


def _beginning_of_day() -> datetime.datetime:
    return datetime.datetime.combine(
        datetime.date.today(),
        datetime.datetime.min.time(),
    )


def revoke_moderator(user: ForumUser, num_visits: int, last_month: datetime):
    logger.debug(f"Revoking {user.username} moderator rights")
    subject = (
        "Sorry, wiwik is revoking your moderator rights since you are not there enough"
    )
    template = loader.get_template("emails/moderator_revoke.html")
    html = template.render(
        context={
            "last_month": last_month,
            "unsubscribe_link": unsubscribe_link_with_base(user),
            "num_visits": num_visits,
            "user": user,
        }
    )
    notify_user.notify_user_email(user, subject, subject, html, True)
    user.is_moderator = False
    user.save()


def grant_moderator(user: ForumUser, num_visits: int, last_month: datetime):
    logger.debug(f"Granting {user.username} moderator rights")
    subject = "Congratulations, you have been active on wiwik so it is granting you moderator rights"
    template = loader.get_template("emails/moderator_grant.html")
    html = template.render(
        context={
            "last_month": last_month,
            "unsubscribe_link": unsubscribe_link_with_base(user),
            "num_visits": num_visits,
            "user": user,
        }
    )
    notify_user.notify_user_email(user, subject, subject, html, True)
    user.is_moderator = True
    user.save()


def _generate_questions_report_for_user(user: ForumUser, bom: datetime):
    # Generate questions report for user since the beginning of the month
    tags = viewutils.get_user_followed_tags(user)
    if len(tags) == 0:
        logger.debug(
            f"User {user.username} does not follow any tags, skipping sending digest"
        )
        # todo send notification to watch some tags? should be only once.
        return ""
    tag_words = [tag.tag_word for tag in tags]
    report_html = recent_questions_email_report(bom, tag_words, skip_if_empty=False)
    if report_html == "":
        logger.debug(
            f"Report for {user.username} has nothing in it, skipping sending digest"
        )
        return ""
    return report_html


def send_warning_loosing_moderator_status_to_user(
    user: ForumUser, num_visits: int, bom: datetime
) -> None:
    """
    Send user a warning about loosing moderator status and a list of questions created
    since the beginning of the month.

    Args:
        user: user to send to
        num_visits: Number of days user visited since the beginning of the month
        bom: beginning of the month

    Returns:
        None
    """
    logger.debug(
        f"Moderator {user.username} visited {num_visits} days this month - sending warning"
    )
    questions_report = _generate_questions_report_for_user(user, bom)
    template = loader.get_template("emails/moderator_revoke_warning.html")
    moderator_revoke_warning = template.render(
        context={
            "num_visits": num_visits,
            "min_days_required": settings.DAYS_TO_REVOKE_MODERATOR,
            "user": user,
        }
    )
    unsubscribe_link = unsubscribe_link_with_base(user)
    html = generate_report_html(
        "",
        [
            moderator_revoke_warning,
            questions_report,
        ],
        unsubscribe_link,
    )
    subject = "The wiwik community missed you, visit more and moderate content"
    notify_user.notify_user_email(user, subject, subject, html, True)


@job("cron")
def update_moderator_status_for_users():
    """
    This method goes through all users and check how many days they visited wiwik in the past month.
    If they visited less than settings.DAYS_TO_REVOKE_MODERATOR => it sends them a notification and
    remove moderator status.
    If they visited settings.DAYS_TO_GRANT_MODERATOR days or more => it sends them a notification
    and grant them moderator status.

    Returns:
        None
    """
    last_month = _beginning_of_day() - datetime.timedelta(days=30)
    user_qs = ForumUser.objects.filter(
        is_superuser=False, is_staff=False, is_active=True
    ).annotate(
        num_visits=Count("uservisit", filter=Q(uservisit__visit_date__gte=last_month))
    )
    for user in user_qs:
        # Revoke moderator status from users who didn't visit enough
        if user.is_moderator and user.num_visits < settings.DAYS_TO_REVOKE_MODERATOR:
            revoke_moderator(user, user.num_visits, last_month)
        # grant moderator status if users visited often
        elif (
            not user.is_moderator
            and user.num_visits >= settings.DAYS_TO_GRANT_MODERATOR
        ):
            grant_moderator(user, user.num_visits, last_month)


@job("cron")
def warn_users_loosing_moderator_status():
    """
    For every user - check number of days the user visited since the beginning of the month.
    If less than settings.DAYS_TO_REVOKE_MODERATOR, sends a warning about possibility to
    loose moderator status.

    Returns:

    """
    logger.debug("Checking moderators that did not visit enough this month")
    beginning_of_month = _beginning_of_day().replace(day=1)
    moderator_qs = ForumUser.objects.filter(
        is_moderator=True, is_superuser=False, is_staff=False, is_active=True
    ).annotate(
        num_visits=Count(
            "uservisit", filter=Q(uservisit__visit_date__gte=beginning_of_month)
        )
    )
    for moderator in moderator_qs:
        if moderator.num_visits < settings.DAYS_TO_REVOKE_MODERATOR:
            send_warning_loosing_moderator_status_to_user(
                moderator, moderator.num_visits, beginning_of_month
            )
