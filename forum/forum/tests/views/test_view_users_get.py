import json

from forum.tests.base import ForumApiTestCase


class TestUsersGet(ForumApiTestCase):
    def test_users_get__return_users_info(self):
        self.client.login(self.usernames[2], self.password)
        query = f"{self.usernames[2]},{self.usernames[1]}"
        res = self.client.users_get(query)
        self.assertIsNotNone(res)
        results = json.loads(res.content.decode("utf-8"))["results"]
        self.assertIsNotNone(results)
        self.assertEqual(2, len(results))
