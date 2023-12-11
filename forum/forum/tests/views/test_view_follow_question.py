from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from wiwik_lib.views.follow_views import create_follow


class TestFollowQuestionView(ForumApiTestCase):

    def setUp(self):
        super().setUp()
        self.question = utils.create_question(self.users[0], self.title, self.question_content, ','.join(self.tags))

    def test_follow_question__green(self):
        self.client.login(self.usernames[1], self.password)
        self.assertEqual(1, self.question.follows.count())
        # act
        res = self.client.follow_question(self.question.pk)
        # assert
        self.assertEqual(2, self.question.follows.count())
        self.assertContains(res, 'Unfollow')

    def test_follow_question__when_already_following__should_do_nothing(self):
        create_follow(self.question, self.users[1])
        self.client.login(self.usernames[1], self.password)
        self.assertEqual(2, self.question.follows.count())
        # act
        res = self.client.follow_question(self.question.pk)
        # assert
        self.assertEqual(2, self.question.follows.count())
        self.assertContains(res, 'Unfollow')

    def test_follow_question__not_existing_question__should_do_nothing(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.follow_question(self.question.pk + 5)
        # assert
        self.assertEqual(1, self.question.follows.count())
        assert_url_in_chain(res, reverse('forum:list'))


class TestUnfollowQuestionView(ForumApiTestCase):

    def setUp(self):
        super().setUp()
        self.question = utils.create_question(self.users[0], self.title, self.question_content, ','.join(self.tags))

    def test_unfollow_question__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.unfollow_question(self.question.pk)
        # assert
        self.assertEqual(0, self.question.follows.count())
        self.assertContains(res, 'Follow')

    def test_unfollow_question__when_already_not_following__should_do_nothing(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.unfollow_question(self.question.pk)
        # assert
        self.assertEqual(1, self.question.follows.count())
        self.assertContains(res, 'Follow')

    def test_unfollow_question__not_existing_question__should_do_nothing(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.unfollow_question(self.question.pk + 5)
        # assert
        self.assertEqual(1, self.question.follows.count())
        assert_url_in_chain(res, reverse('forum:list'))
