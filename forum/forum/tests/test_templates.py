from bs4 import BeautifulSoup

from forum.tests.base import ForumApiTestCase
from userauth.models import ForumUser


class TestTemplates(ForumApiTestCase):
    username1 = "myusername1"
    password = "magicalPa$$w0rd"
    title = "my_question_title"
    question_content = "my_question_content"
    answer_content = "answer---content"
    tags = [
        "my_first_tag",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f"{cls.username1}@a.com", cls.password)

    def test_questions_list__has_footer(self):
        # act
        res = self.client.questions_list(tab="latest")
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("footer")))

    def test_users_list__has_footer(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.users_list()
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("footer")))
