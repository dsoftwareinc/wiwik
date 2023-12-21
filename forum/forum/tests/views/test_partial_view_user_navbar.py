from bs4 import BeautifulSoup
from django.urls import reverse

from forum.models import QuestionBookmark
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestUserNavbarPartialView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(
            cls.users[0], cls.title, cls.question_content, ",".join(cls.tags)
        )
        cls.answer = utils.create_answer(
            cls.answer_content, cls.users[1], cls.question, False
        )
        QuestionBookmark.objects.create(user=cls.users[1], question=cls.question)

    def test_user_navbar_partial_view__should_show_bookmarks__when_user_has(self):
        self.client.login(self.usernames[1], self.password)
        res = self.client.user_navbar()
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, "html.parser")

        bookmark_url = reverse("forum:thread", kwargs={"pk": self.question.pk})
        self.assertEqual(1, len(soup.select(f'a[href="{bookmark_url}"]')))

    def test_user_navbar_partial_view__should_show_no_bookmarks__when_user_has_none(
        self,
    ):
        self.client.login(self.usernames[0], self.password)
        res = self.client.user_navbar()
        self.assertEqual(200, res.status_code)

        self.assertContains(res, "No bookmarks")
