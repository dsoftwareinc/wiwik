import datetime

from constance import config
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestAcceptAnswerView(ForumApiTestCase):
    question: models.Question
    answer: models.Answer

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ",".join(cls.tags))
        cls.answer2 = utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        cls.answer3 = utils.create_answer(cls.answer_content, cls.users[0], cls.question)
        cls.answer = utils.create_answer(cls.answer_content, cls.users[2], cls.question)
        cls.question_pk = cls.question.pk
        cls.answer_pk = cls.answer.pk

    def test_accept_answer_view__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertTrue(q.has_accepted_answer)
        self.assertTrue(a.is_accepted)
        self.assertEqual(1, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))
        activity_len = models.VoteActivity.objects.filter(
            source=self.users[0],
            target=a.author,
            question=q,
            answer=a,
            type=models.VoteActivity.ActivityType.ACCEPT,
        ).count()
        self.assertEqual(1, activity_len)

    def test_accept_answer_view__another_answer_already_accepted(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        self.client.accept_answer(self.question_pk, self.answer2.pk)
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertTrue(q.has_accepted_answer)
        self.assertTrue(a.is_accepted)
        self.assertEqual(1, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))
        activity_len = models.VoteActivity.objects.filter(
            source=self.users[0],
            target=a.author,
            question=q,
            type=models.VoteActivity.ActivityType.ACCEPT,
        ).count()
        self.assertEqual(1, activity_len)

    def test_accept_answer_view__user_not_loggedin(self):
        # arrange
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertFalse(q.has_accepted_answer)
        self.assertFalse(a.is_accepted)
        self.assertEqual(0, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(
            res,
            reverse("userauth:login") + "?next=" + reverse("forum:answer_accept", args=[q.pk, a.pk]),
        )

    def test_accept_answer_view__bad_question_pk(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.accept_answer(self.question_pk + 1, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertFalse(q.has_accepted_answer)
        self.assertFalse(a.is_accepted)
        self.assertEqual(0, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:list"))

    def test_accept_answer_view__bad_answer_pk(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk + 5)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertFalse(q.has_accepted_answer)
        self.assertFalse(a.is_accepted)
        self.assertEqual(0, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))

    def test_accept_answer_view__question_not_by_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertFalse(q.has_accepted_answer)
        self.assertFalse(a.is_accepted)
        self.assertEqual(0, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))

    def test_accept_answer_view__answer_to_different_question(self):
        # arrange
        q = utils.create_question(self.users[1], self.title, self.question_content, ",".join(self.tags))
        a = utils.create_answer(self.answer_content, self.users[0], q)
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.accept_answer(self.question_pk, a.pk)
        # assert
        a = models.Answer.objects.get(pk=a.pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertFalse(q.has_accepted_answer)
        self.assertFalse(a.is_accepted)
        self.assertEqual(0, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))

    @override_settings(DAYS_FOR_QUESTION_TO_BECOME_OLD=2)
    def test_accept_answer__answer_for_old_question__different_user_rep_change(self):
        # arrange
        self.question.created_at = timezone.now() - datetime.timedelta(
            days=config.DAYS_FOR_QUESTION_TO_BECOME_OLD + 1
        )
        self.question.save()
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.accept_answer(self.question_pk, self.answer_pk)
        # assert
        a = models.Answer.objects.get(pk=self.answer_pk)
        q = models.Question.objects.get(pk=self.question_pk)
        self.assertTrue(q.has_accepted_answer)
        self.assertTrue(a.is_accepted)
        self.assertEqual(1, q.answer_set.filter(is_accepted=True).count())
        assert_url_in_chain(res, reverse("forum:thread", args=[q.pk]))
        activity_len = models.VoteActivity.objects.filter(
            source=self.users[0],
            target=a.author,
            question=q,
            answer=a,
            type=models.VoteActivity.ActivityType.ACCEPT_OLD,
        ).count()
        self.assertEqual(1, activity_len)
