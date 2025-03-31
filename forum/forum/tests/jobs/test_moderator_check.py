"""
Tests for:
- warn_users_loosing_moderator_status
- update_moderator_status_for_users
"""

from datetime import date
from unittest import mock

from constance import config

from common.test_utils import assert_not_called_with
from forum.jobs import (
    warn_users_loosing_moderator_status,
    update_moderator_status_for_users,
)
from forum.tests.base import ForumApiTestCase
from userauth.models import ForumUser, UserVisit


class FakeDate(date):
    """A manipulable date replacement"""

    def __new__(cls, *args, **kwargs):
        return date.__new__(date, *args, **kwargs)


class TestModeratorJobs(ForumApiTestCase):
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ForumUser.objects.exclude(username=cls.usernames[2]).update(is_moderator=True)
        UserVisit.objects.create(
            user=cls.users[0],
            visit_date="2021-10-12",
            consecutive_days=1,
        )
        UserVisit.objects.create(
            user=cls.users[0],
            visit_date="2021-10-10",
            consecutive_days=1,
        )
        UserVisit.objects.create(
            user=cls.users[2],
            visit_date="2021-10-12",
            consecutive_days=1,
        )
        UserVisit.objects.create(
            user=cls.users[2],
            visit_date="2021-10-10",
            consecutive_days=1,
        )
        UserVisit.objects.create(
            user=cls.users[2],
            visit_date="2021-10-09",
            consecutive_days=1,
        )
        config.DAYS_TO_REVOKE_MODERATOR = 2
        config.DAYS_TO_GRANT_MODERATOR = 3

    @mock.patch("datetime.date", FakeDate)
    @mock.patch("forum.jobs.notify_user.notify_user_email")
    def test_warn_users_loosing_moderator_status__green(self, notify_user_email: mock.MagicMock):
        # arrange
        subject = "The wiwik community missed you, visit more and moderate content"
        FakeDate.today = classmethod(lambda cls: date(2021, 10, 15))
        # act
        warn_users_loosing_moderator_status()
        # assert
        notify_user_email.assert_called_with(self.users[1], subject, subject, mock.ANY, True)
        assert_not_called_with(notify_user_email, self.users[0], mock.ANY, mock.ANY, mock.ANY, mock.ANY)
        assert_not_called_with(notify_user_email, self.users[2], mock.ANY, mock.ANY, mock.ANY, mock.ANY)

    @mock.patch("datetime.date", FakeDate)
    @mock.patch("forum.jobs.notify_user.notify_user_email")
    def test_update_moderator_status_for_users__green(self, notify_user_email: mock.MagicMock):
        # arrange
        revoke_subject = "Sorry, wiwik is revoking your moderator rights since you are not there enough"
        grant_subject = "Congratulations, you have been active on wiwik so it is granting you moderator rights"
        FakeDate.today = classmethod(lambda cls: date(2021, 11, 1))
        # act
        update_moderator_status_for_users()
        # assert
        for u in self.users:
            u.refresh_from_db()
        notify_user_email.assert_has_calls(
            [
                mock.call(self.users[1], revoke_subject, revoke_subject, mock.ANY, True),
                mock.call(self.users[2], grant_subject, grant_subject, mock.ANY, True),
            ],
            any_order=True,
        )
        assert_not_called_with(notify_user_email, self.users[0], mock.ANY, mock.ANY, mock.ANY, mock.ANY)
        self.assertTrue(self.users[0].is_moderator)
        self.assertFalse(self.users[1].is_moderator)
        self.assertTrue(self.users[2].is_moderator)
