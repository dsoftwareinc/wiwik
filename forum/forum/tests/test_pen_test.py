from forum.tests.base import ForumApiTestCase


class TestSearch(ForumApiTestCase):
    def test_question_with_javascript(self):
        self.client.login(self.users[0], self.password)
        res = self.client.add_question_post(
            "Secura Pentest Cross Site Scripting",
            "<script>alert('Secura XSS test')</script>",
            "",
        )
        self.assertEqual(200, res.status_code)
        self.assertNotContains(res, "<script>alert")
