from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, tag

from userauth.models import ForumUser


@tag('management_command')
class SendWeeklyDigestTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "send_weekly_digest",
            '--no-color',
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ForumUser.objects.create_user('user1', 'user1@a.com')

    def test__user_does_not_exist__exit(self):
        params = '-f 2020-01-01 --username bad_user --file x.html'
        # act
        out = self.call_command(params.split(' '))
        # assert
        self.assertEqual('User bad_user not found\n', out)

    @mock.patch("builtins.open", create=True)
    def test__to_file__green(self, file_mock: mock.MagicMock):
        params = '-f 2020-01-01 --username user1 --file x.html'
        # act
        out = self.call_command(params.split(' '))
        # assert
        self.assertEqual('', out)
        file_mock.assert_called_once_with('x.html', 'w')

    def test__to_email__green(self):
        params = '-f 2020-01-01 --username user1 --email a@a.com'
        # act
        out = self.call_command(params.split(' '))
        # assert
        self.assertEqual('', out)
