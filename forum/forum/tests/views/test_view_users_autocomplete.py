import json

from forum.tests.base import ForumApiTestCase


class TestUsersAutocompleteView(ForumApiTestCase):
    def test_users_autocomplete__when_given_username__should_return_all_users_besides_logged_in(
        self,
    ):
        self.client.login(self.usernames[2], self.password)
        query = self.usernames[2][:-1]
        # act
        res = self.client.users_autocomplete(query)
        # assert
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))["results"]
        self.assertIsNotNone(results)
        self.assertEqual(2, len(results))
        self.assertEqual([], list(filter(lambda x: x["username"] == self.usernames[2], results)))

    def test_users_autocomplete__when_given_name_and_selected__should_return_1_users(
        self,
    ):
        self.client.login(self.usernames[2], self.password)
        query = self.usernames[2][:-1]
        selected = self.usernames[1]
        # act
        res = self.client.users_autocomplete(query, selected=selected)
        # assert
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))["results"]
        self.assertIsNotNone(results)
        self.assertEqual(1, len(results))
        self.assertEqual([], list(filter(lambda x: x["username"] == self.usernames[2], results)))
        self.assertEqual([], list(filter(lambda x: x["username"] == self.usernames[1], results)))

    def test_users_autocomplete__when_no_matching_users__should_return_nothing(self):
        self.client.login(self.usernames[2], self.password)
        query = "longstring"
        # act
        res = self.client.users_autocomplete(query)
        # assert
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))["results"]
        self.assertIsNotNone(results)
        self.assertEqual(0, len(results))
