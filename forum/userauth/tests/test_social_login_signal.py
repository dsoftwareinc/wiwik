import os

from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.test.utils import override_settings

from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase
from userauth.views import populate_profile, fill_missing_data_in_profile
from wiwik_lib.adapters import CustomSocialAccountAdapter


class UserAuthLoginTest(UserAuthTestCase):
    username1 = "myusername1"
    username2 = "myusername2"
    username_no_social = "no_social"
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(
            cls.username1, f"{cls.username1}@a.com", cls.password
        )
        cls.user2 = ForumUser.objects.create_user(
            cls.username2, f"{cls.username2}@a.com", cls.password
        )
        cls.user_no_social = ForumUser.objects.create_user(
            cls.username_no_social,
            f"{cls.username_no_social}@a.com",
            cls.password,
            name=cls.username_no_social,
        )
        cls.extra_data = {
            "id": "100466292043055079210",
            "email": "danielmo@backbase.com",
            "verified_email": True,
            "name": "Daniel Moran",
            "given_name": "Daniel",
            "family_name": "Moran",
            "link": "https://plus.google.com/100466292043055079210",
            "picture": "https://lh3.googleusercontent.com/a-/AOh14GhJ_MtvscWtf-"
            "1mWCYS43nIM5CdykiTiIbxl25y=s96-c",
            "locale": "en",
            "hd": "backbase.com",
        }
        cls.socialaccount1 = SocialAccount.objects.create(
            user=cls.user1,
            provider="google",
            uid=cls.extra_data["id"],
            extra_data=cls.extra_data,
        )

        cls.socialaccount2 = SocialAccount.objects.create(
            user=cls.user1,
            provider="facebook",
            uid=cls.extra_data["id"],
            extra_data=cls.extra_data,
        )

    def test_user_signed_up__green(self):
        # arrange
        social_login = SocialLogin(self.user1, self.socialaccount1)
        # act
        populate_profile(
            social_login,
            self.user1,
        )
        # assert
        self.user1.refresh_from_db()
        self.assertEqual(self.extra_data["email"], self.user1.email)
        self.assertEqual(self.extra_data["name"], self.user1.name)
        self.assertIn(
            f"profile_pic_{self.username1}.google", self.user1.profile_pic.path
        )
        # cleanup
        os.remove(self.user1.profile_pic.path)

    def test_user_signed_up__no_socialaccount__should_not_populate(self):
        # arrange
        social_login = SocialLogin(self.user_no_social, self.socialaccount1)
        # act
        populate_profile(
            social_login,
            self.user_no_social,
        )
        # assert
        self.user_no_social.refresh_from_db()
        self.assertEqual(f"{self.username_no_social}@a.com", self.user_no_social.email)
        self.assertEqual(self.username_no_social, self.user_no_social.name)
        self.assertIn(
            os.path.join(settings.MEDIA_ROOT, "default_pics/default_image.jpg"),
            self.user_no_social.profile_pic.path,
        )

    def test_user_signed_up__bad_socialaccount__should_not_populate(self):
        # arrange
        social_login = SocialLogin(self.user2, self.socialaccount2)
        # act
        populate_profile(
            social_login,
            self.user2,
        )
        # assert
        self.user2.refresh_from_db()
        self.assertEqual(f"{self.username2}@a.com", self.user2.email)
        self.assertIsNone(self.user2.name)
        self.assertIn(
            os.path.join(settings.MEDIA_ROOT, "default_pics/default_image.jpg"),
            self.user2.profile_pic.path,
        )

    def test_user_logged_in__green(self):
        # arrange
        social_login = SocialLogin(self.user1, self.socialaccount1)
        old_path = self.user1.profile_pic.path
        # act
        fill_missing_data_in_profile(
            social_login,
            self.user1,
        )
        # assert
        self.user1.refresh_from_db()
        self.assertEqual(old_path, self.user1.profile_pic.path)

    def test_user_logged_in__bad_socialaccount__should_not_populate(self):
        # arrange
        social_login = SocialLogin(self.user2, self.socialaccount2)
        # old_path = self.user1.profile_pic.path
        # act
        fill_missing_data_in_profile(
            social_login,
            self.user2,
        )
        # assert
        self.user2.refresh_from_db()
        self.assertEqual(f"{self.username2}@a.com", self.user2.email)
        self.assertIsNone(self.user2.name)
        self.assertIn(
            os.path.join(settings.MEDIA_ROOT, "default_pics/default_image.jpg"),
            self.user2.profile_pic.path,
        )

    def test_user_logged_in__profile_pic_exists__should_not_populate(self):
        # arrange
        social_login = SocialLogin(self.user1, self.socialaccount1)
        self.user1.profile_pic = settings.MEDIA_ROOT + "/BadImage.jpeg"
        self.user1.save()
        # act
        fill_missing_data_in_profile(
            social_login,
            self.user1,
        )
        # assert
        self.user1.refresh_from_db()
        self.assertIn(
            f"profile_pic_{self.username1}.google", self.user1.profile_pic.path
        )
        # cleanup
        os.remove(self.user1.profile_pic.path)

    @override_settings(ALLOWED_REGISTRATION_EMAIL_DOMAINS=None)
    def test_socialaccount_adapter__no_limited_domains__green(self):
        # arrange
        adapter = CustomSocialAccountAdapter()
        sociallogin = SocialLogin(user=self.user1)
        request = self.client.get("/customer/details").wsgi_request
        # act
        adapter.pre_social_login(request, sociallogin)
        # assert

    @override_settings(ALLOWED_REGISTRATION_EMAIL_DOMAINS="b.com")
    def test_socialaccount_adapter__limited_domains_not_allowed__green(self):
        # arrange
        adapter = CustomSocialAccountAdapter()
        sociallogin = SocialLogin(user=self.user1)
        request = self.client.get("/customer/details").wsgi_request
        # act
        try:
            adapter.pre_social_login(request, sociallogin)
            self.fail("PermissionDenied error expected")
        except PermissionDenied:
            pass
        # assert

    @override_settings(ALLOWED_REGISTRATION_EMAIL_DOMAINS="a.com")
    def test_socialaccount_adapter__limited_domains_allowed__green(self):
        # arrange
        adapter = CustomSocialAccountAdapter()
        sociallogin = SocialLogin(user=self.user1)
        request = self.client.get("/customer/details").wsgi_request
        # act
        try:
            adapter.pre_social_login(request, sociallogin)
        except PermissionDenied:
            self.fail("PermissionDenied error was not expected")
        # assert
