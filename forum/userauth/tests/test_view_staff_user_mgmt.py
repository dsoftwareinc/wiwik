from userauth.models import ForumUser
from userauth.tests.utils import UserAuthTestCase


class UserAuthViewStaffDeactivateUser(UserAuthTestCase):
    staff_username = "staff_member"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ForumUser.objects.create_user(
            cls.staff_username,
            f"{cls.staff_username}@a.com",
            cls.password,
            is_staff=True,
        )

    def test_view_staff_deactivate_user__green(self):
        # arrange
        self.client.login(self.staff_username, self.password)

        # act
        res = self.client.staff_deactivate_user(self.usernames[0])

        # assert
        self.assertEqual(200, res.status_code)
        self.users[0].refresh_from_db()
        self.assertFalse(self.users[0].is_active)

    def test_view_staff_deactivate_user__not_staff__should_403(self):
        # arrange
        self.client.login(self.users[1].username, self.password)

        # act
        res = self.client.staff_deactivate_user(self.usernames[0])

        # assert
        self.assertEqual(403, res.status_code)
        self.users[0].refresh_from_db()
        self.assertTrue(self.users[0].is_active)

    def test_view_staff_deactivate_user__non_existing_user__should_404(self):
        # arrange
        self.client.login(self.staff_username, self.password)

        # act
        res = self.client.staff_deactivate_user(self.usernames[0] + "sss")

        # assert
        self.assertEqual(404, res.status_code)


class UserAuthViewStaffActivateUser(UserAuthTestCase):
    staff_username = "staff_member"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ForumUser.objects.create_user(
            cls.staff_username,
            f"{cls.staff_username}@a.com",
            cls.password,
            is_staff=True,
        )
        cls.users[0].is_active = False
        cls.users[0].save()

    def test_view_staff_activate_user__green(self):
        # arrange
        self.client.login(self.staff_username, self.password)

        # act
        res = self.client.staff_activate_user(self.usernames[0])

        # assert
        self.assertEqual(200, res.status_code)
        self.users[0].refresh_from_db()
        self.assertTrue(self.users[0].is_active)

    def test_view_staff_activate_user__not_staff__should_403(self):
        # arrange
        self.client.login(self.users[1].username, self.password)

        # act
        res = self.client.staff_activate_user(self.usernames[0])

        # assert
        self.assertEqual(403, res.status_code)
        self.users[0].refresh_from_db()
        self.assertFalse(self.users[0].is_active)

    def test_view_staff_activate_user__non_existing_user__should_404(self):
        # arrange
        self.client.login(self.staff_username, self.password)

        # act
        res = self.client.staff_activate_user(self.usernames[0] + "sss")

        # assert
        self.assertEqual(404, res.status_code)
