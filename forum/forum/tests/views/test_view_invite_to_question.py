from django.urls import reverse

from common.test_utils import assert_url_in_chain, assert_message_in_response
from forum.models import PostInvitation
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from userauth.models import ForumUser


class TestInviteToQuestionView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
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
        cls.question = utils.create_question(cls.user1, cls.title, cls.question_content, ','.join(cls.tags))

    def test_invite_to_question__non_existing_user__green(self):
        # arrange
        self.client.login(self.username2, self.password)
        username = "myusername5"
        # act
        res = self.client.invite_to_question_post(self.question.pk, username)
        # assert
        self.assertEqual(0, PostInvitation.objects.all().count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))

    def test_invite_to_question__when_post_request__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.invite_to_question_post(self.question.pk, self.username2)
        # assert
        self.assertEqual(1, PostInvitation.objects.all().count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))
        assert_message_in_response(res, "Successfully invited user(s) to this question.")

    def test_invite_to_question__bad_question__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        bad_question_pk = self.question.pk + 25
        # act
        res = self.client.invite_to_question_post(bad_question_pk, self.username2)
        # assert
        self.assertEqual(0, PostInvitation.objects.all().count())
        assert_url_in_chain(res, reverse('forum:thread', args=[bad_question_pk, ]))

    def test_invite_to_question__when_get_request__should_redirect_to_question_page(self):
        # arrange
        self.client.login(self.username2, self.password)
        # act
        res = self.client.invite_to_question_get(self.question.pk)
        # assert
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))

    def test_invite_to_question__invite_self__not_created(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.invite_to_question_post(self.question.pk, self.username1)
        # assert
        self.assertEqual(0, PostInvitation.objects.all().count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))
