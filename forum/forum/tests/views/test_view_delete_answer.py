from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestDeleteAnswerView(ForumApiTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ",".join(cls.tags))

    def setUp(self):
        super().setUp()
        utils.create_answer(self.answer_content, self.users[1], self.question)
        self.answer2 = utils.create_answer(self.answer_content, self.users[0], self.question)
        self.answer = utils.create_answer(self.answer_content, self.users[2], self.question)
        utils.upvote(self.users[0], self.answer)
        utils.upvote(self.users[1], self.answer)

    def test_delete_answer__delete_accepted_answer__question_should_be_without_has_accepted(
        self,
    ):
        # arrange
        self.answer.is_accepted = True
        self.answer.save()
        self.question.has_accepted_answer = True
        self.question.save()
        self.client.login(self.usernames[2], self.password)
        pk = self.answer.pk
        previous_last_activity = self.question.last_activity
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.question.refresh_from_db()
        self.assertEqual(0, models.Answer.objects.filter(pk=pk).count())
        self.assertEqual(2, self.question.answer_set.count())
        self.assertFalse(self.question.has_accepted_answer)
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, previous_last_activity)

    def test_delete_answer__delete_non_accepted_answer__question_should_be_with_accepted(
        self,
    ):
        # arrange
        self.answer2.is_accepted = True
        self.answer2.save()
        self.question.has_accepted_answer = True
        self.question.save()
        self.client.login(self.usernames[2], self.password)
        pk = self.answer.pk
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.question.refresh_from_db()
        self.assertEqual(0, models.Answer.objects.filter(pk=pk).count())
        self.assertEqual(2, self.question.answer_set.count())
        self.assertTrue(self.question.has_accepted_answer)

    def test_delete_answer_confirmation_page__green(self):
        # arrange
        self.client.login(self.usernames[2], self.password)
        # act
        res = self.client.delete_answer_confirmation_page(self.question.pk, self.answer.pk)
        # assert
        self.question.refresh_from_db()
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, self.question.answer_set.count())
        self.assertEqual(
            f"/question/{self.question.pk}/delete/{self.answer.pk}",
            res.request["PATH_INFO"],
        )

    def test_delete_answer__green(self):
        # arrange
        self.client.login(self.usernames[2], self.password)
        answer = models.Answer.objects.get(pk=self.answer.pk)
        previous_reputation = answer.author.reputation_score
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(0, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(2, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        self.users[2].refresh_from_db()
        self.assertEqual(previous_reputation - 20, self.users[2].reputation_score)
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]))

    def test_delete_answer__user_not_logged_in(self):
        # arrange
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse("forum:answer_delete", args=[self.question.pk, self.answer.pk]),
        )

    def test_delete_answer__answer_owned_by_different_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]))

    def test_delete_answer__answer_does_not_exist(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk + 5)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]))

    def test_delete_answer__answer_is_for_different_question(self):
        # arrange
        q = utils.create_question(self.users[0], self.title, self.question_content, ",".join(self.tags))
        a = utils.create_answer(self.answer_content, self.users[0], q)
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_answer(self.question.pk, a.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse("forum:thread", args=[self.question.pk]))
