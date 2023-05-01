import os

from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase


class UserAuthEditProfileTest(UserAuthTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    password = 'magicalPa$$w0rd'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2 = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)

    def test_profile_pic_post__user_upload_new_profile_pic__should_redirect(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        base64_string = "R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
        image_data = f"data:image/png;base64,{base64_string}"
        self.client.profile_pic_post(image_data)
        res = self.client.edit_profile_get()
        # assert
        assert res.status_code == 200
        # clean
        self.user1.refresh_from_db()
        os.remove(self.user1.profile_pic.path)

    def test_profile_pic_get__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.profile_pic_get()
        # assert
        assert res.status_code == 200
        body = str(res.content)
        assert "profile-pic-modal" in body
