from bs4 import BeautifulSoup
from django.conf import settings

from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestPostCommentsPartialView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(
            cls.users[0], cls.title, cls.question_content, ",".join(cls.tags)
        )
        cls.answer = utils.create_answer(
            cls.answer_content, cls.users[1], cls.question, False
        )

    def test_comments_partial_view__question_max_comments_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = "comment------content"
        settings.MAX_COMMENTS = 3
        for _ in range(settings.MAX_COMMENTS):
            self.client.thread_add_comment(
                self.question.pk, "question", self.question.pk, comment_content
            )
        # act
        res = self.client.view_partial_post_comments("question", self.question.pk)
        # assert
        self.assertContains(res, "Maximum number of comments reached", status_code=200)

    def test_comments_partial_view__question_max_comments_not_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = "comment------content"
        settings.MAX_COMMENTS = 3
        for _ in range(settings.MAX_COMMENTS - 1):
            self.client.thread_add_comment(
                self.question.pk, "question", self.question.pk, comment_content
            )
        # act
        res = self.client.view_partial_post_comments("question", self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertNotContains(res, "Maximum number of comments reached")
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(
            1,
            len(
                soup.find_all(
                    "form",
                    {
                        "class": "form-add-comment",
                        "model": "question",
                        "pk": self.question.pk,
                    },
                )
            ),
        )
        self.assertEqual(
            1,
            len(
                soup.find_all(
                    "div",
                    {
                        "class": "add-comment-button",
                        "model": "question",
                        "pk": self.question.pk,
                    },
                )
            ),
        )

    def test_comments_partial_view__answer_max_comments_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = "comment------content"
        settings.MAX_COMMENTS = 3
        for _ in range(settings.MAX_COMMENTS):
            self.client.thread_add_comment(
                self.question.pk, "answer", self.answer.pk, comment_content
            )
        # act
        res = self.client.view_partial_post_comments("answer", self.answer.pk)
        # assert
        self.assertContains(res, "Maximum number of comments reached", status_code=200)

    def test_comments_partial_view__answer_max_comments_not_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = "comment------content"
        settings.MAX_COMMENTS = 3
        for _ in range(settings.MAX_COMMENTS - 1):
            self.client.thread_add_comment(
                self.question.pk, "answer", self.answer.pk, comment_content
            )
        # act
        res = self.client.view_partial_post_comments("answer", self.answer.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertNotContains(res, "Maximum number of comments reached")
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(
            1,
            len(
                soup.find_all(
                    "form",
                    {
                        "class": "form-add-comment",
                        "model": "answer",
                        "pk": self.question.pk,
                    },
                )
            ),
        )
        self.assertEqual(
            1,
            len(
                soup.find_all(
                    "div",
                    {
                        "class": "add-comment-button",
                        "model": "answer",
                        "pk": self.question.pk,
                    },
                )
            ),
        )
