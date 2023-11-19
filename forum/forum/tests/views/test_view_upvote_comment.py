from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestUpvoteCommentView(ForumApiTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))
        cls.answer = utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        cls.qcomment = utils.create_comment(cls.comment_content, cls.users[2], cls.question)
        cls.acomment = utils.create_comment(cls.comment_content, cls.users[0], cls.answer)

    def test_upvote_comment_for_question__green(self):
        self.client.login(self.usernames[0], self.password)
        last_activity = self.question.last_activity
        # act
        res = self.client.upvote_comment(self.question.pk, 'question', self.qcomment.pk)
        # assert
        comment = models.QuestionComment.objects.get(pk=self.qcomment.pk)
        self.assertEqual(1, comment.votes)
        assert_url_in_chain(
            res,
            reverse('forum:thread', args=[self.question.pk, ]) + f'#question_{self.question.pk}')
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, last_activity)

    def test_upvote_comment_for_answer__green(self):
        self.client.login(self.usernames[1], self.password)
        last_activity = self.question.last_activity
        # act
        res = self.client.upvote_comment(self.question.pk, 'answer', self.acomment.pk)
        # assert
        comment = models.AnswerComment.objects.get(pk=self.acomment.pk)
        self.assertEqual(1, comment.votes)
        assert_url_in_chain(
            res,
            reverse('forum:thread', args=[self.question.pk, ]) + f'#answer_{self.answer.pk}')
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, last_activity)

    def test_upvote_comment_for_answer__same_user__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        self.question.refresh_from_db()
        last_activity = self.question.last_activity
        # act
        res = self.client.upvote_comment(self.question.pk, 'answer', self.acomment.pk)
        # assert
        comment = models.AnswerComment.objects.get(pk=self.acomment.pk)
        self.assertEqual(0, comment.votes)
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, last_activity)

    def test_upvote_comment_for_answer__already_upvoted__should_do_nothing(self):
        comment = models.AnswerComment.objects.get(pk=self.acomment.pk)
        utils.upvote_comment(self.users[1], comment)
        self.question.refresh_from_db()
        last_activity = self.question.last_activity
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.upvote_comment(self.question.pk, 'answer', self.acomment.pk)
        # assert

        self.assertEqual(1, comment.votes)
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, last_activity)
