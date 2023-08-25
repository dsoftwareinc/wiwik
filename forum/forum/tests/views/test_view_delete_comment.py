from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from userauth.models import ForumUser


class TestDeleteCommentView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    comment_content = 'comment_content_yada_ddd'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2 = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)
        cls.user3 = ForumUser.objects.create_user(cls.username3, f'{cls.username3}@a.com', cls.password)
        q = utils.create_question(cls.user1, cls.title, cls.question_content, ','.join(cls.tags))
        a = utils.create_answer(cls.answer_content, cls.user3, q)
        cls.question = q
        cls.answer = a

    def setUp(self):
        super().setUp()
        utils.create_comment(self.comment_content, self.user2, self.question)
        utils.create_comment(self.comment_content, self.user2, self.answer)
        utils.create_comment(self.comment_content, self.user1, self.question)
        utils.create_comment(self.comment_content, self.user1, self.answer)

    def test_delete_question_comment__green(self):
        # arrange
        previous_count = self.question.comments.count()
        comment = self.question.comments.first()
        self.client.login(comment.author.username, self.password)

        # act
        res = self.client.delete_comment(self.question.pk, 'question', comment.id)
        # assert
        self.assertEqual(previous_count - 1, self.question.comments.count())
        anchor = f'#question_{self.question.pk}'
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]) + anchor)

    def test_delete_answer_comment__green(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.first()
        self.client.login(comment.author.username, self.password)

        # act
        res = self.client.delete_comment(self.question.pk, 'answer', comment.id)
        # assert
        self.assertEqual(previous_count - 1, self.answer.comments.count())
        anchor = f'#answer_{self.answer.pk}'
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]) + anchor)

    def test_delete_question__user_not_logged_in(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.first()
        # act
        res = self.client.delete_comment(self.question.pk, 'answer', comment.pk)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' +
                            reverse('forum:comment_delete',
                                    args=[self.question.pk, 'answer', comment.pk])
                            )

    def test_delete_comment__comment_owned_by_different_user(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.filter(author_id=self.user1.pk).first()
        self.client.login(self.username2, self.password)
        # act
        res = self.client.delete_comment(self.question.pk, 'answer', comment.pk)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        anchor = f'#answer_{self.answer.pk}'
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]) + anchor)

    def test_delete_comment__comment_does_not_exist(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.filter(author_id=self.user1.pk).first()
        self.client.login(self.username2, self.password)
        # act
        res = self.client.delete_comment(self.question.pk, 'answer', comment.pk + 4)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))
