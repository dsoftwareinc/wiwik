import bs4
from django.core import mail
from django.test.utils import override_settings
from django.urls import reverse

from common.test_utils import assert_url_in_chain, assert_message_in_response
from userauth import models
from userauth.tests.utils import UserAuthTestCase
from wiwik_lib.utils import set_current_site


class UserAuthSignupTest(UserAuthTestCase):
    @override_settings(
        ADMINS=[
            ("wiwik-admin", "a@a.com"),
        ]
    )
    def test_signup__green(self):
        set_current_site()
        from wiwik_lib.utils import CURRENT_SITE
        user_email = "u1@a.com"
        res = self.client.signup_post("u1", "u1_display_name", user_email, "Cunld2332")

        # assert user created
        assert res.status_code == 200
        assert_url_in_chain(res, reverse("forum:home"))
        self.assertEqual(1, models.ForumUser.objects.filter(username="u1").count())
        self.assertEqual(
            1,
            models.ForumUserAdditionalData.objects.filter(user__username="u1").count(),
        )
        self.assertEqual(2, len(mail.outbox))

        self.assertEqual("Activate your forum account", mail.outbox[0].subject)
        self.assertIn("u1@a.com", mail.outbox[0].to)
        self.assertIn("u1_display_name", mail.outbox[0].body)

        self.assertEqual(
            f"[Django] {user_email} registered to {CURRENT_SITE}",
            mail.outbox[1].subject,
        )
        assert_message_in_response(
            res,
            "New account created: u1, Please confirm your email address to complete the registration",
        )
        soup = bs4.BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("div", {"class": "userauth-messages"})))
        msgs_element = soup.find_all("div", {"class": "userauth-messages"})[0]
        self.assertEqual(1, len(msgs_element.find_all("div")))
        self.assertContains(
            res,
            """<div class="alert alert-success alert-dismissible fade show" role="alert">
New account created: u1, Please confirm your email address to complete the registration
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>""",
            html=True,
        )

    @override_settings(ADMINS=None)
    def test_signup__no_admins_to_notify(self):
        res = self.client.signup_post("u1", "u1_display_name", "u1@a.com", "Cunld2332")
        # assert user created
        assert res.status_code == 200
        assert_url_in_chain(res, reverse("forum:home"))
        self.assertEqual(1, models.ForumUser.objects.filter(username="u1").count())
        self.assertEqual(
            1,
            models.ForumUserAdditionalData.objects.filter(user__username="u1").count(),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, "Activate your forum account")
        self.assertIn("u1@a.com", mail.outbox[0].to)
        self.assertIn("u1_display_name", mail.outbox[0].body)
        assert_message_in_response(
            res,
            "New account created: u1, Please confirm your email address to complete the registration",
        )

    @override_settings(ALLOWED_REGISTRATION_EMAIL_DOMAINS="a.com")
    def test_signup__email_not_allowed(self):
        res = self.client.signup_post("u0", "u0", "a@b.com", "cunld233")
        # assert user not created
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "email domain not allowed")
        soup = bs4.BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("div", {"class": "userauth-messages"})))
        msgs_element = soup.find_all("div", {"class": "userauth-messages"})[0]
        self.assertEqual(1, len(msgs_element.find_all("div")))
        self.assertContains(
            res,
            """<div class="alert alert-danger error alert-dismissible fade show" role="alert">
email domain not allowed
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>""",
            html=True,
        )

    def test_signup__bad_email(self):
        res = self.client.signup_post("u0", "u0", "bad_email", "cunld233")
        # assert user not created
        self.assertEqual(0, models.ForumUser.objects.filter(username="u0").count())
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "Enter a valid email address.")
        self.assertContains(
            res,
            """<div class="alert alert-danger error alert-dismissible fade show" role="alert">
Enter a valid email address.
<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
</div>""",
            html=True,
        )

    def test_signup__passwords_mismatch(self):
        res = self.client.signup_post("user2", "u2", "u2@a.com", "cunld233", "cunld2332233")
        # assert user not created
        self.assertEqual(0, models.ForumUser.objects.filter(username="u2").count())
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "The two password fields didn’t match.")

    def test_signup__bad_password(self):
        res = self.client.signup_post("user2", "u2", "u2@a.com", "1111", "1111")
        # assert user not created
        self.assertEqual(0, models.ForumUser.objects.filter(username="u2").count())
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "This password is too short. It must contain at least 8 characters.")
        assert_message_in_response(res, "This password is too common.")
        assert_message_in_response(res, "This password is entirely numeric.")

    def test_signup__username_exists(self):
        self.client.signup_post("u0", "u0", "u0@a.com", "cunld233")
        res = self.client.signup_post("u0", "name", "u220@a.com", "cunld233")
        # assert user not created
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, models.ForumUser.objects.filter(username="u0").count())

    def test_signup__email_exists(self):
        self.client.signup_post("user_email_exists", "user_email_exists", "email@a.com", "cunld233")
        res = self.client.signup_post("another_user", "u0", "email@a.com", "cunld233")
        # assert user not created
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, models.ForumUser.objects.filter(username="user_email_exists").count())
        self.assertEqual(0, models.ForumUser.objects.filter(username="another_user").count())
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "email already registered, you can reset your password")

    def test_signup__user_not_logged_in(self):
        # act
        res = self.client.signup_get()
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, len([i[0] for i in res.redirect_chain]))

    def test_signup__user_logged_in(self):
        # arrange
        self.client.signup_and_login("user", "user", "u@a.com", "cunssd222ds")
        # act
        res = self.client.signup_get()
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse("forum:list"))
