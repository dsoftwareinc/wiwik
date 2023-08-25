from io import StringIO

from django.core import management
from django.test import TransactionTestCase
from django.test.utils import override_settings

from userauth import models


@override_settings(SKIP_USER_VISIT_LOG=True)
class CreateSampleUsersTest(TransactionTestCase):

    def call_command(self, *args, **kwargs):
        out = StringIO()
        management.call_command(
            "create_sample_users",
            '--no-color',
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test__green(self):
        # act
        out = self.call_command()
        # assert
        self.assertEqual(11, models.ForumUser.objects.count())
        self.assertEqual('', out)

    def test__admin_user_exists(self):
        # arrange
        models.ForumUser.objects.create_superuser('admin', 'a@a.com', '1111')
        # act
        out = self.call_command()
        # assert
        self.assertEqual('Could not create admin\n', out)

    def test__user1_user_exists(self):
        # arrange
        models.ForumUser.objects.create_superuser('user1', 'user1@a.com', '1111')
        # act
        out = self.call_command()
        # assert
        self.assertEqual('Could not create user1\n', out)
