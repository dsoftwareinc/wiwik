from datetime import datetime, timedelta

from django.core import mail
from django.test import override_settings

from userauth.jobs import log_request
from userauth.models import UserVisit, ForumUser
from userauth.tests.utils import UserAuthTestCase


class UserAuthAdminTest(UserAuthTestCase):
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )

    def test_admin_uservisit_changelist__filter__green(self):
        # arrange
        UserVisit.objects.create(
            user=self.users[0],
            visit_date="2021-10-21",
            consecutive_days=1,
        )
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("uservisit", query="q=2021-10-21")
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, self.usernames[0])

    def test_admin_user_changelist__filter__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("forumuser")
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, self.usernames[0])

    def test_admin_user_single_user__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_change("forumuser", self.users[0].id)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, self.usernames[0])

    def test_admin_action_send_email__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        data = {
            "action": "send_email",
            "_selected_action": ForumUser.objects.all().values_list("pk", flat=True),
        }
        # act
        res = self.client.admin_changelist_post("forumuser", data=data)
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_action_send_email_form__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        prev_len = len(mail.outbox)
        subject = "subject"
        message = "message"
        # act
        self.client.send_email_post(
            [
                self.users[0].id,
            ],
            subject,
            message,
        )
        # assert
        self.assertEqual(len(mail.outbox), prev_len + 1)
        self.assertEqual(mail.outbox[-1].subject, subject)
        self.assertEqual(mail.outbox[-1].body, message)

    @override_settings(DEBUG=True)
    def test_admin_action_send_email_form__debug_mode__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        prev_len = len(mail.outbox)
        subject = "subject"
        message = "message"
        # act
        self.client.send_email_post(
            [
                self.users[0].id,
            ],
            subject,
            message,
        )
        # assert
        self.assertEqual(len(mail.outbox), prev_len + 1)
        self.assertEqual(
            mail.outbox[-1].to,
            [
                "style.daniel@gmail.com",
            ],
        )
        self.assertEqual(mail.outbox[-1].subject, subject)
        self.assertEqual(mail.outbox[-1].body, message)

    def test_admin_action_deactivate_users__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        data = {
            "action": "deactivate_users",
            "_selected_action": ForumUser.objects.exclude(id=self.superuser.id).values_list("pk", flat=True),
        }
        # act
        res = self.client.admin_changelist_post("forumuser", data=data)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, ForumUser.objects.filter(is_active=True).count())
        self.assertEqual(len(self.users), ForumUser.objects.filter(is_active=False).count())

    def test_admin_action_grant_moderator__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(0, ForumUser.objects.filter(is_moderator=True).count())
        data = {
            "action": "action_grant_moderator",
            "_selected_action": ForumUser.objects.exclude(id=self.superuser.id).values_list("pk", flat=True),
        }
        # act
        res = self.client.admin_changelist_post("forumuser", data=data)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(len(self.users), ForumUser.objects.filter(is_moderator=True).count())
        self.assertEqual(1, ForumUser.objects.filter(is_moderator=False).count())

    def test_admin_action_grant_moderator__inactive_user__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(0, ForumUser.objects.filter(is_moderator=True).count())
        self.users[0].is_active = False
        self.users[0].save()
        data = {
            "action": "action_grant_moderator",
            "_selected_action": ForumUser.objects.exclude(id=self.superuser.id).values_list("pk", flat=True),
        }
        # act
        res = self.client.admin_changelist_post("forumuser", data=data)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(len(self.users) - 1, ForumUser.objects.filter(is_moderator=True).count())
        self.assertEqual(2, ForumUser.objects.filter(is_moderator=False).count())

    def test_admin_action_cleanup_visits__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        for u in self.users:
            for d in range(4):
                log_request(
                    u.id,
                    "127.0.0.1",
                    datetime.now() - timedelta(days=d),
                    100,
                    "method",
                    "/path",
                )
        for u in self.users:
            self.assertEqual(4, UserVisit.objects.filter(user=u).count())
        data = {
            "action": "action_user_visits_cleanup",
            "_selected_action": ForumUser.objects.exclude(id=self.superuser.id).values_list("pk", flat=True),
        }
        # act
        res = self.client.admin_changelist_post("forumuser", data=data)
        # assert
        self.assertEqual(200, res.status_code)
        for u in self.users:
            self.assertEqual(1, UserVisit.objects.filter(user=u).count())
