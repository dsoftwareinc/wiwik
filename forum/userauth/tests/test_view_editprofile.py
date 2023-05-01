from django.urls import reverse

from common.test_utils import assert_url_in_chain, assert_message_in_response
from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase


class UserAuthEditProfileTest(UserAuthTestCase):
    username1 = 'myusername1'
    password = 'magicalPa$$w0rd'
    name = 'Little engine'
    title = 'Master of wars'
    about_me = 'Creating chaos'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password,
                                                  name=cls.name, title=cls.title,
                                                  about_me=cls.about_me)

    def test_editprofile_get__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_profile_get()
        # assert
        assert res.status_code == 200
        self.assertContains(res, self.username1)
        self.assertContains(res, self.user1.name)
        self.assertContains(res, 'croppie.min.js"></script>')

    def test_editprofile_get__user_not_authenticated__should_redirect(self):
        # act
        res = self.client.edit_profile_get()
        # assert
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' + reverse('userauth:edit'))

    def test_editprofile_post__green(self):
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_profile_post('new name', 'new title', 'new about', 'on')
        # assert
        self.assertEqual(200, res.status_code)
        self.user1.refresh_from_db()
        self.assertEqual('new name', self.user1.name)
        self.assertEqual('new title', self.user1.title)
        self.assertEqual('new about', self.user1.about_me)
        self.assertTrue(self.user1.email_notifications)

    def test_editprofile_post__no_title__should_update_all_but_title(self):
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_profile_post('new name', '', 'new about', 'on')
        # assert
        self.assertEqual(200, res.status_code)
        self.user1.refresh_from_db()
        self.assertEqual('new name', self.user1.name)
        self.assertEqual(self.title, self.user1.title)
        self.assertEqual('new about', self.user1.about_me)
        self.assertTrue(self.user1.email_notifications)

    def test_editprofile_post__empty_info__should_update_nothing(self):
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_profile_post('', '', '', 'on')
        # assert
        self.assertEqual(200, res.status_code)
        self.user1.refresh_from_db()
        self.assertEqual(self.name, self.user1.name)
        self.assertEqual(self.title, self.user1.title)
        self.assertEqual(self.about_me, self.user1.about_me)
        self.assertTrue(self.user1.email_notifications)

    def test_editprofile_post__name_too_long__should_fail(self):
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_profile_post('name' + 'n' * 100, '', 'new about', 'on')
        # assert
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "Expected value length between 1..100 for fullname but got 104")
        self.user1.refresh_from_db()
        self.assertEqual(self.name, self.user1.name)
        self.assertEqual(self.title, self.user1.title)
        self.assertEqual(self.about_me, self.user1.about_me)
        self.assertTrue(self.user1.email_notifications)
