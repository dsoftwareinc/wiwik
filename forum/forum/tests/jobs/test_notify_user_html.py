from datetime import timedelta
from unittest.mock import patch

from django.utils import timezone

from forum import jobs
from forum.tests.base import ForumApiTestCase
from userauth.models import ForumUser


class TestUsersAutocompleteView(ForumApiTestCase):
    username = 'myusername1'
    password = 'magicalPa$$w0rd'
    subject = 'subject'
    text = 'text'
    html = '<div>html</div>'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = ForumUser.objects.create_user(cls.username, f'{cls.username}@a.com', cls.password)

    @patch('django.core.mail.EmailMessage.send')
    def test_notify_user_email__green(self, mock):
        # arrange
        self.user.email_notifications = True
        self.user.last_email_datetime = None
        self.user.save()
        # act
        jobs.notify_user_email(self.user, self.subject, self.text, self.html, True)
        # assert
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.last_email_datetime)
        mock.assert_called_once()

    @patch('forum.jobs.notify_user.send_email_async')
    def test_notify_user_email__user_email_notifications_off__not_sending(self, mock):
        # arrange
        self.user.email_notifications = False
        self.user.save()
        # act
        jobs.notify_user_email(self.user, self.subject, self.text, self.html, True)
        # assert
        self.user.refresh_from_db()
        mock.assert_not_called()

    @patch('forum.jobs.notify_user.send_email_async')
    def test_notify_user_email__unimportant_notification_and_recently_had_one__not_sending(self, mock):
        # arrange
        self.user.email_notifications = True
        last_email_datetime = timezone.now() - timedelta(minutes=55)
        self.user.last_email_datetime = last_email_datetime
        self.user.save()

        # act
        jobs.notify_user_email(self.user, self.subject, self.text, self.html, False)
        # assert
        self.user.refresh_from_db()
        self.assertEqual(last_email_datetime, self.user.last_email_datetime)
        mock.assert_not_called()
