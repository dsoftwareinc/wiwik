import json

from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestUsersAutocompleteView(ForumApiTestCase):
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))

    def test_users_autocomplete__when_given_username__should_return_3_users(self):
        self.client.login(self.usernames[2], self.password)
        query = self.usernames[2][:-1]
        # act
        res = self.client.users_autocomplete(query)
        # assert
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))['results']
        self.assertIsNotNone(results)
        self.assertEqual(3, len(results))

    def test_users_autocomplete__when_no_matching_users__should_return_nothing(self):
        self.client.login(self.usernames[2], self.password)
        query = 'longstring'
        # act
        res = self.client.users_autocomplete(query)
        # assert
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))['results']
        self.assertIsNotNone(results)
        self.assertEqual(0, len(results))
