from forum.models import VoteActivity
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestAcceptAnswerView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ",".join(cls.tags))
        cls.activity = VoteActivity.objects.create(
            source=None,
            target=cls.users[0],
            reputation_change=10,
            question=cls.question,
            type=VoteActivity.ActivityType.UPVOTE,
        )

    def test_view_all_mark_as_seen__green(self):
        self.client.login(self.usernames[0], self.password)
        self.activity.seen = None
        self.activity.save()
        # act
        res = self.client.mark_all_as_seen()
        # assert
        self.assertEqual(200, res.status_code)
        self.activity.refresh_from_db()
        self.assertIsNotNone(self.activity.seen)

    def test_view_mark_as_seen__green(self):
        self.activity.seen = None
        self.activity.save()
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.mark_as_seen(self.activity.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.activity.refresh_from_db()
        self.assertIsNotNone(self.activity.seen)

    def test_view_mark_as_seen__not_target__return_forbidden(self):
        self.activity.seen = None
        self.activity.save()
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.mark_as_seen(self.activity.pk)
        # assert
        self.assertEqual(403, res.status_code)
        self.activity.refresh_from_db()
        self.assertIsNone(self.activity.seen)

    def test_view_mark_as_seen__not_exist__return_not_found(self):
        self.activity.seen = None
        self.activity.save()
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.mark_as_seen(self.activity.pk + 5)
        # assert
        self.assertEqual(404, res.status_code)
        self.activity.refresh_from_db()
        self.assertIsNone(self.activity.seen)
