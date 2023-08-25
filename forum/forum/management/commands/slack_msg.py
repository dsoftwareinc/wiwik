from django.core.management.base import CommandParser

from wiwik_lib.utils import ManagementCommand
from forum.integrations import slack_api


class Command(ManagementCommand):
    help = 'Send slack message'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-t', '--text', type=str, required=True,
                            help='Text to post to channel')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-c', '--channel', type=str,
                           help='Channel to post msg to')
        group.add_argument('-e', '--email', type=str,
                           help='email to post msg to')

    def handle(self, text: str, channel: str, email: str, *args, **options):
        if email:
            slack_api.slack_post_im_message_to_email(text, email)
        else:
            slack_api.slack_post_channel_message(text, channel)
