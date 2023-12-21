from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestDeleteCommentView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        q = utils.create_question(cls.users[0], cls.title, cls.question_content, ",".join(cls.tags))
        a = utils.create_answer(cls.answer_content, cls.users[2], q)
        cls.question = q
        cls.answer = a

    def setUp(self):
        super().setUp()
        utils.create_comment(self.comment_content, self.users[1], self.question)
        utils.create_comment(self.comment_content, self.users[1], self.answer)
        utils.create_comment(self.comment_content, self.users[0], self.question)
        utils.create_comment(self.comment_content, self.users[0], self.answer)

    def test_delete_question_comment__green(self):
        # arrange
        previous_count = self.question.comments.count()
        comment = self.question.comments.first()
        self.client.login(comment.author.username, self.password)

        # act
        res = self.client.delete_comment(self.question.pk, "question", comment.id)
        # assert
        self.assertEqual(previous_count - 1, self.question.comments.count())
        anchor = f"#question_{self.question.pk}"
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]) + anchor)

    def test_delete_answer_comment__green(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.first()
        self.client.login(comment.author.username, self.password)

        # act
        res = self.client.delete_comment(self.question.pk, "answer", comment.id)
        # assert
        self.assertEqual(previous_count - 1, self.answer.comments.count())
        anchor = f"#answer_{self.answer.pk}"
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]) + anchor)

    def test_delete_question__user_not_logged_in(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.first()
        # act
        res = self.client.delete_comment(self.question.pk, "answer", comment.pk)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse("forum:comment_delete", args=[self.question.pk, "answer", comment.pk]),
        )

    def test_delete_comment__comment_owned_by_different_user(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.filter(author_id=self.users[0].pk).first()
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_comment(self.question.pk, "answer", comment.pk)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        anchor = f"#answer_{self.answer.pk}"
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]) + anchor)

    def test_delete_comment__comment_does_not_exist(self):
        # arrange
        previous_count = self.answer.comments.count()
        comment = self.answer.comments.filter(author_id=self.users[0].pk).first()
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_comment(self.question.pk, "answer", comment.pk + 4)
        # assert
        self.assertEqual(previous_count, self.answer.comments.count())
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]))
