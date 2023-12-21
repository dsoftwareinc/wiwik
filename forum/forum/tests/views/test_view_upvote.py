from django.conf import settings
from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestUpvoteView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(
            cls.users[0], cls.title, cls.question_content, ",".join(cls.tags)
        )
        cls.answer_same_user = utils.create_answer(
            "answer---content", cls.users[0], cls.question
        )
        cls.answer_diff_user = utils.create_answer(
            "answer---content", cls.users[1], cls.question
        )
        cls.prev_last_activity = cls.question.last_activity

    def test_upvote_question__green(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.upvote(self.question.pk, "question", self.question.pk)
        # assert
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#question_{self.question.pk}",
        )
        self.question.refresh_from_db()
        self.assertEqual(1, self.question.votes)
        self.assertEqual(settings.UPVOTE_CHANGE, self.question.author.reputation_score)
        vote_activity_list = list(models.VoteActivity.objects.all())
        item = vote_activity_list[0]
        self.assertEqual(1, len(vote_activity_list))
        self.assertEqual(self.usernames[1], item.source.username)
        self.assertEqual(self.question.author, item.target)
        self.assertEqual(None, item.answer)
        self.assertEqual(self.question, item.question)
        self.assertEqual(settings.UPVOTE_CHANGE, item.reputation_change)
        self.assertGreater(self.question.last_activity, self.prev_last_activity)

    def test_upvote_answer__green(self):
        self.client.login(self.usernames[0], self.password)

        # act
        res = self.client.upvote(self.question.pk, "answer", self.answer_diff_user.pk)
        # assert
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#answer_{self.answer_diff_user.pk}",
        )
        a = models.Answer.objects.get(pk=self.answer_diff_user.pk)
        self.assertEqual(1, a.votes)
        self.assertEqual(settings.UPVOTE_CHANGE, a.author.reputation_score)
        vote_activity_list = list(models.VoteActivity.objects.all())
        self.assertEqual(1, len(vote_activity_list))
        item = vote_activity_list[0]
        self.assertEqual(self.users[0], item.source)
        self.assertEqual(a.author, item.target)
        self.assertEqual(a, item.answer)
        self.assertEqual(self.question, item.question)
        self.assertEqual(settings.UPVOTE_CHANGE, item.reputation_change)
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, self.prev_last_activity)

    def test_upvote_answer__for_same_user__should_not_upvote(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.upvote(self.question.pk, "answer", self.answer_same_user.pk)
        # assert
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#answer_{self.answer_same_user.pk}",
        )
        self.answer_same_user.refresh_from_db()
        self.assertEqual(0, self.answer_same_user.votes)
        self.assertEqual(0, self.answer_same_user.author.reputation_score)
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, self.prev_last_activity)

    def test_upvote_answer__when_downvoted(self):
        utils.downvote(self.users[0], self.answer_diff_user)
        previous_reputation = self.users[1].reputation_score
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.upvote(self.question.pk, "answer", self.answer_diff_user.pk)
        # assert
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#answer_{self.answer_diff_user.pk}",
        )
        a = (
            models.Answer.objects.filter(id=self.answer_diff_user.pk)
            .prefetch_related("author", "author__additional_data")
            .first()
        )
        self.assertEqual(1, a.votes)
        self.assertEqual(
            previous_reputation + settings.UPVOTE_CHANGE - settings.DOWNVOTE_CHANGE,
            a.author.reputation_score,
        )
        vote_activity_list = list(models.VoteActivity.objects.all())
        self.assertEqual(1, len(vote_activity_list))
        item = vote_activity_list[0]
        self.assertEqual(self.users[0], item.source)
        self.assertEqual(a.author, item.target)
        self.assertEqual(a, item.answer)
        self.assertEqual(self.question, item.question)
        self.assertEqual(settings.UPVOTE_CHANGE, item.reputation_change)
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, self.prev_last_activity)

    def test_upvote_answer__when_already_upvoted(self):
        utils.upvote(self.users[0], self.answer_diff_user)
        previous_reputation = self.users[1].reputation_score
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.upvote(self.question.pk, "answer", self.answer_diff_user.pk)
        # assert
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#answer_{self.answer_diff_user.pk}",
        )
        a = (
            models.Answer.objects.filter(id=self.answer_diff_user.pk)
            .prefetch_related("author", "author__additional_data")
            .first()
        )
        self.assertEqual(
            previous_reputation - settings.UPVOTE_CHANGE, a.author.reputation_score
        )
        self.assertEqual(0, models.VoteActivity.objects.all().count())
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, self.prev_last_activity)
