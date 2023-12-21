from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, tag


@tag("management_command")
class SendSlackMsgTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "slack_msg",
            "--no-color",
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    @mock.patch("forum.integrations.slack_api.slack_post_im_message_to_email")
    def test__im_send__green(self, method: mock.MagicMock):
        # act
        out = self.call_command("-t", "text to send", "-e", "a@a.com")
        # assert
        self.assertEqual("", out)
        method.assert_called_once_with("text to send", "a@a.com")

    @mock.patch("forum.integrations.slack_api.slack_post_channel_message")
    def test__channel_send__green(self, method: mock.MagicMock):
        # act
        out = self.call_command("-t", "text to send", "-c", "#everything")
        # assert
        self.assertEqual("", out)
        method.assert_called_once_with("text to send", "#everything")
