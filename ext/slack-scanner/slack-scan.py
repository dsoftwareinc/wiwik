import json
import logging
import os
from collections import namedtuple
from datetime import datetime
from typing import Dict, Optional, List

from dotenv import load_dotenv, find_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

load_dotenv(find_dotenv())
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN', None)
SLACK_NOTIFICATIONS_CHANNEL = os.getenv('SLACK_NOTIFICATIONS_CHANNEL', None)
SLACK_SIGNING_SECRET_KEY = os.getenv('SLACK_SIGNING_SECRET_KEY', None)

logger = logging.getLogger(__package__)
logging.basicConfig(level=logging.INFO)

SlackUserInfo = namedtuple('SlackUserInfo', ['name', 'username', 'email', 'image_url', ])
MessageInfo = namedtuple('MessageInfo', ['user', 'ts', 'text'])


class SlackCrawler(object):

    def __init__(self, token: str):
        self.client = WebClient(SLACK_BOT_TOKEN)
        self.threads_dict: Dict[str, List[MessageInfo]] = dict()
        self.users_dict: Dict[str, SlackUserInfo] = dict()
        self.channel_map: Dict[str, str] = dict()
        self._scan_channels()

    def _scan_channels(self) -> Dict[str, str]:
        """
        Scan all channels that can be read and returns a dictionary from
        channel name to its id.
        Requires permissions (https://api.slack.com/messaging/retrieving):
            - channels:read
            - channels:history

        Returns:
            Dictionary Channel name => Channel ID.
        """
        try:
            response = self.client.conversations_list()
            self.channel_map = {
                channel["name"]: channel["id"] for channel in response["channels"]
            }
            return self.channel_map
        except SlackApiError as e:
            logger.error("Error fetching conversations: {}".format(e))
            raise e

    def get_channels(self) -> List[str]:
        return list(self.channel_map.keys())

    def _channel_history(self, channel_name: str) -> List[str]:
        """Returns list of thread ids in channel
        # https://api.slack.com/methods/conversations.history$pagination
        """
        channel_id = self.channel_map.get(channel_name, None)
        if channel_id is None:
            logger.error(f'channel_id for channel {channel_name} not found; '
                         f'{len(self.channel_map)} channels are mapped')
        logger.debug(f'Scanning history for {channel_name} (id={channel_id})')
        cursor = None
        threads_list = list()
        try:
            while True:
                result = self.client.conversations_history(channel=channel_id, cursor=cursor)
                logger.debug(f"{len(result['messages'])} messages found in #{channel_name}")
                threads_list.extend([
                    item['thread_ts']
                    for item in result['messages']
                    if 'thread_ts' in item
                ])
                cursor = result.get('response_metadata', dict()).get('next_cursor', None)
                if not cursor:
                    break
            logger.debug(f"{len(threads_list)} threads found in #{channel_name}")
            return threads_list
        except SlackApiError as e:
            logger.error(f"Error getting channel history for #{channel_name}: {e}")
            raise e

    def _analyze_thread(self, channel_name: str, thread_ts: str):
        channel_id = self.channel_map[channel_name]
        try:
            res = self.client.conversations_replies(channel=channel_id, ts=thread_ts)
            return res['messages']
        except SlackApiError as e:
            logger.error(f"Error getting channel history for #{channel_name}: {e}")
            raise e

    def get_user_info(self, slack_user_id: str) -> Optional[SlackUserInfo]:
        """
        requires: users:read.email, users:read
        """
        if slack_user_id in self.users_dict:
            return self.users_dict[slack_user_id]
        try:
            response = self.client.users_info(user=slack_user_id)
            if not response['ok']:
                logger.warning(f"Couldn't find slack user {slack_user_id}, slack error: {response['error']}")
                return None
            profile = response.get('user', {}).get('profile', {})
            if not profile:
                logger.warning(f"Couldn't find slack user {slack_user_id}. response from slack_api: {response}")
                return None
            self.users_dict[slack_user_id] = SlackUserInfo(
                profile.get('real_name', None),
                response.get('user', {}).get('name', None),
                profile.get('email', None),
                profile.get('image_original', None),
            )
            return self.users_dict[slack_user_id]
        except SlackApiError as e:
            logger.warning(f"Couldn't find slack user {slack_user_id}, slack error: {e.response['error']}")
            return None

    def read_channel_threads(self, channel_name: str) -> None:
        """Scan a channel threads and users and populate self.threads_dict and self.users_dict accordingly.

        Returns:
           None
        """
        users_set = set()
        threads_list = self._channel_history(channel_name)
        logger.debug(f'Getting info for {len(threads_list)} threads')
        for thread_ts in threads_list:
            thread = self._analyze_thread(channel_name, thread_ts)
            users_set.update(thread[0]['reply_users'])
            users_set.add(thread[0]['user'])
            self.threads_dict[thread_ts] = [
                MessageInfo(i['user'], datetime.fromtimestamp(int(float(i['ts']))).isoformat(), i['text'])
                for i in thread
            ]
        logger.debug(f'Getting info for {len(users_set)} users')
        for user in users_set:
            self.get_user_info(user)


if __name__ == '__main__':
    channel = 'everything'
    if not SLACK_BOT_TOKEN:
        logger.error("SLACK_BOT_TOKEN not set, exiting")
        raise EnvironmentError("slack-client not initialized, can't scan")
    crawler = SlackCrawler(SLACK_BOT_TOKEN)
    print(crawler.get_channels())

    crawler.read_channel_threads(channel)
    print(json.dumps(crawler.threads_dict, indent=2))
    print(json.dumps(crawler.users_dict, indent=2))
