from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from common.test_utils import assert_message_in_response, assert_url_in_chain
from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase
from userauth.views.tokens import account_activation_token


class UserAuthActivateTest(UserAuthTestCase):
    username1 = 'magical_username'
    password = 'magicalPa$$w0rd'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)

    def test_activate__green(self):
        self.user1.is_active = False
        self.user1.save()
        user_id_base64 = urlsafe_base64_encode(force_bytes(self.user1.pk))
        activation_key = account_activation_token.make_token(self.user1)
        # act
        res = self.client.activate_user(user_id_base64, activation_key)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('userauth:login'))
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.is_active)
        assert_message_in_response(
            res,
            'Account activated successfully. Thank you '
            'for your email confirmation. Now you can login your account.')

    def test_activate__non_existing_user__should_fail(self):
        user_id_base64 = urlsafe_base64_encode(force_bytes(self.user1.pk + 1))
        activation_key = account_activation_token.make_token(self.user1)
        # act
        res = self.client.activate_user(user_id_base64, activation_key)
        # assert
        assert res.status_code == 200
        assert_url_in_chain(res, reverse('userauth:login'))
        assert_message_in_response(res, 'Activation link is invalid!')

    def test_activate__bad_activation_key__should_fail(self):
        user_id_base64 = urlsafe_base64_encode(force_bytes(self.user1.pk))
        activation_key_bad_token = account_activation_token.make_token(self.user1) + 'x'
        # act
        res = self.client.activate_user(user_id_base64, activation_key_bad_token)
        # assert
        assert res.status_code == 200
        assert_url_in_chain(res, reverse('userauth:login'))
        assert_message_in_response(res, 'Activation link is invalid!')
