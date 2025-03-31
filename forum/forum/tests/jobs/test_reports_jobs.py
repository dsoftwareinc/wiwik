"""
Tests for:
- send_weekly_digest_for_users
- send_daily_activity_report_for_admins
These tests test sending the report to the users,
not the accuracy of the report.
"""

import datetime
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from common.test_utils import assert_not_called_with
from forum import jobs
from forum.jobs import send_daily_activity_report_for_admins
from forum.views import utils, follow_models
from tags.models import Tag
from userauth.models import ForumUser


class TestReportJobs(TestCase):
    usernames = [
        "myusername1",
        "myusername2",
        "myusername3",
    ]
    password = "magicalPa$$w0rd"
    title = "my_question_title"
    question_content = "my_question_content"
    answer_content = "answer---content"
    tags = [
        "my_first_tag",
    ]
    no_activity_tag = "no_activity_tag"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = [
            ForumUser.objects.create_user(username, f"{username}@a.com", cls.password) for username in cls.usernames
        ]
        cls.old_question = utils.create_question(
            cls.users[0],
            cls.title,
            cls.question_content,
            ",".join(cls.tags),
            created_at=timezone.now() - datetime.timedelta(days=10),
        )
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ",".join(cls.tags))
        utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        utils.create_answer(cls.answer_content, cls.users[0], cls.question)
        tag = Tag.objects.create(tag_word=cls.no_activity_tag)
        follow_models.create_follow_tag(tag, cls.users[2])
        cls.fromdate = timezone.now() - datetime.timedelta(days=7)

    @mock.patch("forum.jobs.reports_jobs.weekly_digest_to_user")
    @mock.patch("forum.jobs.notify_user.notify_user_email")
    def test_send_weekly_digest_for_users__green(
        self,
        notify_user: mock.MagicMock,
        single_digest: mock.MagicMock,
    ):
        # arrange
        subject = f"Weekly digest on tags you are following, activity since {self.fromdate.date()}"
        result = "Some result"
        single_digest.return_value = result
        # act
        jobs.send_weekly_digest_for_users()
        # assert
        single_digest.assert_has_calls([mock.call(u, mock.ANY) for u in self.users])
        notify_user.assert_has_calls([mock.call(u, subject, subject, result, True) for u in self.users])

    @mock.patch("forum.jobs.notify_user.notify_user_email")
    def test_send_weekly_digest_for_users__only_users_with_data__should_be_2(
        self,
        notify_user: mock.MagicMock,
    ):
        # arrange
        subject = f"Weekly digest on tags you are following, activity since {self.fromdate.date()}"
        # act
        jobs.send_weekly_digest_for_users()
        # assert
        notify_user.assert_has_calls(
            [
                mock.call(self.users[0], subject, subject, mock.ANY, True),
                mock.call(self.users[1], subject, subject, mock.ANY, True),
            ],
            any_order=True,
        )
        assert_not_called_with(notify_user, self.users[2], subject, subject, mock.ANY, True)

    @mock.patch("django.core.mail.mail_admins")
    def test_send_daily_activity_report_for_admins__green(self, mail_admins: mock.MagicMock):
        # arrange
        fromdate = timezone.now() - datetime.timedelta(days=1)
        subject = f"Daily activity report {fromdate.date()}-{datetime.date.today()}"
        # act
        send_daily_activity_report_for_admins()
        # assert
        mail_admins.assert_called_with(subject, subject, html_message=mock.ANY)
