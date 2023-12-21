from unittest import mock

from common.test_utils import ForumClient, assert_not_called_with
from forum.jobs import calculate_all_users_impact, calculate_user_impact
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from userauth.models import ForumUser


class TestUsersAutocompleteView(ForumApiTestCase):
    question_title = "my question title"
    question_content = "My question content"
    answer_content = "My answer content"
    tags = ["my_first_tag", "my_second_tag", "my_third_tag"]
    superuser_name = "superuser"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.questions = [
            utils.create_question(user, cls.question_title, cls.question_content, ",".join(cls.tags))
            for user in cls.users
        ]
        utils.create_answer(cls.answer_content, cls.users[0], cls.questions[0])
        utils.upvote(cls.users[0], cls.questions[1])
        utils.upvote(cls.users[0], cls.questions[2])
        utils.upvote(cls.users[1], cls.questions[0])
        utils.upvote(cls.users[1], cls.questions[2])
        a = utils.create_answer(cls.answer_content, cls.users[0], cls.questions[1])
        a.is_accepted = True
        a.save()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )
        utils.update_question(
            cls.users[1],
            cls.questions[0],
            cls.question_title + "1",
            cls.question_content,
            ",".join(cls.tags),
        )

    def setUp(self):
        self.client = ForumClient()

    @mock.patch("forum.jobs.user_impact.calculate_user_impact")
    def test_calculating_for_all_users(self, method: mock.MagicMock):
        # arrange
        # act
        calculate_all_users_impact()
        # assert
        method.assert_has_calls([mock.call(u) for u in self.users], any_order=True)
        assert_not_called_with(method, mock.call(self.superuser))

    def test_calculate_user_impact(self):
        # arrange
        user = self.users[1]
        self.questions[1].views = 5
        self.questions[1].save()
        # act
        calculate_user_impact(user)
        # assert
        user.refresh_from_db()
        self.assertEqual(2, user.votes)
        self.assertEqual(5, user.people_reached)
        self.assertEqual(1, user.posts_edited)
