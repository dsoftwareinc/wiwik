from unittest import mock
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase
from slack_sdk.errors import SlackApiError

from forum.integrations import slack_api
from userauth.models import ForumUser


class TestSlackApi(TestCase):
    text = "text"
    channel = "channel"
    email = "a@a.com"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = ForumUser.objects.create_user("user", cls.email, "1111")

    def setUp(self):
        super().setUp()
        settings.SLACK_BOT_TOKEN = "xxx"

    def test_slack_post_channel_message__green(self):
        # arrange
        slack_api.slack_client = MagicMock()
        # act
        slack_api.slack_post_channel_message(self.text, self.channel)
        # assert
        slack_api.slack_client.chat_postMessage.assert_called_once_with(
            channel=self.channel,
            thread_ts=None,
            text=self.text,
            blocks=mock.ANY,
            mrkdwn=True,
        )

    def test_slack_post_channel_message__no_slack_token(self):
        # arrange
        slack_api.slack_client = MagicMock()
        settings.SLACK_BOT_TOKEN = None
        # act
        slack_api.slack_post_channel_message(self.text, self.channel)
        # assert
        slack_api.slack_client.chat_postMessage.assert_not_called()

    def test_slack_post_channel_message__exception(self):
        # arrange
        slack_api.slack_client = MagicMock()
        slack_api.slack_client.chat_postMessage.side_effect = SlackApiError(
            message="message", response={"error": "error"}
        )
        # act
        slack_api.slack_post_channel_message(self.text, self.channel)
        # assert
        slack_api.slack_client.chat_postMessage.assert_called_once_with(
            channel=self.channel,
            thread_ts=None,
            text=self.text,
            blocks=mock.ANY,
            mrkdwn=True,
        )

    def test_slack_post_im_message__green(self):
        # arrange
        user_id = "id"
        slack_api.slack_client = MagicMock()
        slack_api.slack_client.users_lookupByEmail.return_value = {
            "ok": True,
            "user": {"id": user_id},
        }
        # act
        slack_api.slack_post_im_message_to_email(self.text, self.email)
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_called_once_with(email=self.email)
        slack_api.slack_client.chat_postMessage.assert_called_once_with(
            channel=user_id, blocks=mock.ANY, text=self.text, mrkdwn=True
        )

    def test_slack_post_im_message__no_slack_token(self):
        # arrange
        settings.SLACK_BOT_TOKEN = None
        slack_api.slack_client = MagicMock()
        # act
        slack_api.slack_post_im_message_to_email(self.text, self.email)
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_not_called()
        slack_api.slack_client.chat_postMessage.assert_not_called()

    def test_slack_post_im_message__user_not_found_in_slack(self):
        # arrange
        slack_api.slack_client = MagicMock()
        slack_api.slack_client.users_lookupByEmail.return_value = {
            "ok": False,
            "error": "users_not_found",
        }
        # act
        slack_api.slack_post_im_message_to_email(self.text, self.email)
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_called_once_with(email=self.email)
        slack_api.slack_client.chat_postMessage.assert_not_called()

    def test_slack_post_im_message__user_not_found_in_forum(self):
        # arrange
        slack_api.slack_client = MagicMock()
        # act
        slack_api.slack_post_im_message_to_email(self.text, "not_found@a.com")
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_not_called()
        slack_api.slack_client.chat_postMessage.assert_not_called()

    def test_slack_post_im_message__exception_posting_message(self):
        # arrange
        user_id = "id"
        slack_api.slack_client = MagicMock()
        slack_api.slack_client.users_lookupByEmail.return_value = {
            "ok": True,
            "user": {"id": user_id},
        }
        slack_api.slack_client.chat_postMessage.side_effect = SlackApiError(
            message="message", response={"error": "error"}
        )
        # act
        slack_api.slack_post_im_message_to_email(self.text, self.email)
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_called_once_with(email=self.email)
        slack_api.slack_client.chat_postMessage.assert_called_once_with(
            channel=user_id, blocks=mock.ANY, text=self.text, mrkdwn=True
        )

    def test_slack_post_im_message__exception_searching_user(self):
        # arrange
        slack_api.slack_client = MagicMock()
        slack_api.slack_client.users_lookupByEmail.side_effect = SlackApiError(
            message="message", response={"error": "error"}
        )
        # act
        slack_api.slack_post_im_message_to_email(self.text, self.email)
        # assert
        slack_api.slack_client.users_lookupByEmail.assert_called_once_with(email=self.email)
        slack_api.slack_client.chat_postMessage.assert_not_called()
