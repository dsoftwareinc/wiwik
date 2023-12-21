from io import StringIO

from django.core import management
from django.test import TestCase

from userauth.models import ForumUser


class ResetUsersPasswordTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        management.call_command(
            "reset_users",
            "--no-color",
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    def test__green(self):
        # assert
        for i in range(2):
            ForumUser.objects.create_user(
                f"user{i}",
                f"user{i}@so.com",
                f"user{i}",
                name=f"user name {i}",
                title="fancy title",
            )
        # act
        self.call_command()
        # assert
        user_qs = ForumUser.objects.all()
        for u in user_qs:
            self.assertTrue(u.check_password("1111"))
