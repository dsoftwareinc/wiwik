from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from userauth.models import ForumUser
from wiwik_lib.models import Follow
from wiwik_lib.views.follow_views import create_follow


class TestFollowQuestionView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2 = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)
        cls.user3 = ForumUser.objects.create_user(cls.username3, f'{cls.username3}@a.com', cls.password)

    def setUp(self):
        super().setUp()
        self.question = utils.create_question(self.user1, self.title, self.question_content, ','.join(self.tags))

    def test_follow_question__green(self):
        self.client.login(self.username2, self.password)
        self.assertEqual(1, self.question.follows.count())
        # act
        res = self.client.follow_question(self.question.pk)
        # assert
        self.assertEqual(2, self.question.follows.count())
        self.assertContains(res, 'Unfollow')

    def test_follow_question__when_already_following__should_do_nothing(self):
        create_follow(self.question, self.user2)
        self.client.login(self.username2, self.password)
        self.assertEqual(2, self.question.follows.count())
        # act
        res = self.client.follow_question(self.question.pk)
        # assert
        self.assertEqual(2, self.question.follows.count())
        self.assertContains(res, 'Unfollow')

    def test_follow_question__not_existing_question__should_do_nothing(self):
        self.client.login(self.username2, self.password)
        # act
        res = self.client.follow_question(self.question.pk + 5)
        # assert
        self.assertEqual(1, self.question.follows.count())
        assert_url_in_chain(res, reverse('forum:list'))


class TestUnfollowQuestionView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    def setUp(self):
        super().setUp()
        self.user1 = ForumUser.objects.create_user(self.username1, f'{self.username1}@a.com', self.password)
        self.user2 = ForumUser.objects.create_user(self.username2, f'{self.username2}@a.com', self.password)
        self.user3 = ForumUser.objects.create_user(self.username3, f'{self.username3}@a.com', self.password)
        self.question = utils.create_question(self.user1, self.title, self.question_content, ','.join(self.tags))

    def test_unfollow_question__green(self):
        self.client.login(self.username1, self.password)
        # act
        res = self.client.unfollow_question(self.question.pk)
        # assert
        self.assertEqual(0, self.question.follows.count())
        self.assertContains(res, 'Follow')

    def test_unfollow_question__when_already_not_following__should_do_nothing(self):
        self.client.login(self.username2, self.password)
        # act
        res = self.client.unfollow_question(self.question.pk)
        # assert
        self.assertEqual(1, self.question.follows.count())
        self.assertContains(res, 'Follow')

    def test_unfollow_question__not_existing_question__should_do_nothing(self):
        self.client.login(self.username2, self.password)
        # act
        res = self.client.unfollow_question(self.question.pk + 5)
        # assert
        self.assertEqual(1, self.question.follows.count())
        assert_url_in_chain(res, reverse('forum:list'))
