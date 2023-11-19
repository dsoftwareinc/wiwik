from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from common.test_utils import ForumClient
from userauth.models import ForumUser


@override_settings(SKIP_USER_VISIT_LOG=True, SLACK_NOTIFICATIONS_CHANNEL=None)
class ForumApiTestCase(TestCase):
    usernames = ['myuser_name1', 'myuser_name2', 'myuser_name3', ]
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content_with more than 20 chars'
    tags = ['my_first_tag', ]
    answer_content = 'answer------content'
    comment_content = 'comment_content_yada_ddd'
    users: list[ForumUser]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.prev_channel = settings.SLACK_NOTIFICATIONS_CHANNEL
        settings.SLACK_NOTIFICATIONS_CHANNEL = None
        cls.users = [
            ForumUser.objects.create_user(
                username, f'{username}@a.com', cls.password,
            ) for username in cls.usernames]

    def setUp(self):
        self.client = ForumClient()

    @classmethod
    def tearDownClass(cls):
        settings.SLACK_NOTIFICATIONS_CHANNEL = cls.prev_channel
        super().tearDownClass()
