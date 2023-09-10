from django.urls import reverse

from common.test_utils import assert_message_in_response, assert_url_in_chain
from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase


class UserAuthLoginTest(UserAuthTestCase):
    username_non_active = 'my_non_active'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_non_active = ForumUser.objects.create_user(
            cls.username_non_active, f'{cls.username_non_active}@a.com', cls.password, is_active=False, )

    def test_logout__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.logout_get()
        # assert
        assert res.status_code == 200
        assert_url_in_chain(res, reverse('userauth:login'))
        assert_message_in_response(res, 'Logged out successfully!')

    def test_login__green(self):
        # act
        res = self.client.login_post(self.usernames[0], self.password)
        # assert
        assert res.status_code == 200
        assert_url_in_chain(res, reverse('forum:home'))
        assert_message_in_response(res, f"You are logged in as <b>{self.usernames[0]}@a.com</b>")

    def test_login__bad_password__should_fail(self):
        # act
        res = self.client.login_post(self.usernames[0], self.password + '1')
        # assert
        assert res.status_code == 200
        assert_message_in_response(res, "Invalid username or password")

    def test_login__non_active_user__should_fail(self):
        # act
        res = self.client.login_post(self.username_non_active, self.password)
        # assert
        assert res.status_code == 200
        assert_message_in_response(res, "Invalid username or password")

    def test_login__bad_username_should_fail(self):
        # act
        res = self.client.login_post(self.usernames[0] + '1', self.password)
        # assert
        assert res.status_code == 200
        assert_message_in_response(res, "Invalid username or password")

    def test_login__bad_password_should_fail(self):
        # act
        res = self.client.login_post(self.usernames[0], self.password + '1')
        # assert
        assert res.status_code == 200
        assert_message_in_response(res, "Invalid username or password")

    def test_login__bad_next__go_to_home(self):
        # act
        res = self.client.login_post(self.usernames[0], self.password, next='javascript/alert(1)')
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('forum:home'))

    def test_login__when_already_logged_in_should_redirect(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.login_get()
        # assert
        assert res.status_code == 200
        assert_message_in_response(res, "User already logged in")
