from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from userauth.models import ForumUser


class TestDeleteAnswerView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2 = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)
        cls.user3 = ForumUser.objects.create_user(cls.username3, f'{cls.username3}@a.com', cls.password)
        cls.question = utils.create_question(cls.user1, cls.title, cls.question_content, ','.join(cls.tags))

    def setUp(self):
        super().setUp()
        utils.create_answer(self.answer_content, self.user2, self.question)
        self.answer2 = utils.create_answer(self.answer_content, self.user1, self.question)
        self.answer = utils.create_answer(self.answer_content, self.user3, self.question)
        utils.upvote(self.user1, self.answer)
        utils.upvote(self.user2, self.answer)

    def test_delete_answer__delete_accepted_answer__question_should_be_without_has_accepted(self):
        # arrange
        self.answer.is_accepted = True
        self.answer.save()
        self.question.has_accepted_answer = True
        self.question.save()
        self.client.login(self.username3, self.password)
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

    def test_delete_answer__delete_non_accepted_answer__question_should_be_with_accepted(self):
        # arrange
        self.answer2.is_accepted = True
        self.answer2.save()
        self.question.has_accepted_answer = True
        self.question.save()
        self.client.login(self.username3, self.password)
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
        self.client.login(self.username3, self.password)
        # act
        res = self.client.delete_answer_confirmation_page(self.question.pk, self.answer.pk)
        # assert
        self.question.refresh_from_db()
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, self.question.answer_set.count())
        self.assertEqual(f'/question/{self.question.pk}/delete/{self.answer.pk}', res.request['PATH_INFO'])

    def test_delete_answer__green(self):
        # arrange
        self.client.login(self.username3, self.password)
        answer = models.Answer.objects.get(pk=self.answer.pk)
        previous_reputation = answer.author.reputation_score
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(0, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(2, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        self.user3.refresh_from_db()
        self.assertEqual(previous_reputation - 20, self.user3.reputation_score)
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    def test_delete_answer__user_not_logged_in(self):
        # arrange
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' +
                            reverse('forum:answer_delete', args=[self.question.pk, self.answer.pk]))

    def test_delete_answer__answer_owned_by_different_user(self):
        # arrange
        self.client.login(self.username2, self.password)
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    def test_delete_answer__answer_does_not_exist(self):
        # arrange
        self.client.login(self.username2, self.password)
        # act
        res = self.client.delete_answer(self.question.pk, self.answer.pk + 5)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    def test_delete_answer__answer_is_for_different_question(self):
        # arrange
        q = utils.create_question(self.user1, self.title, self.question_content, ','.join(self.tags))
        a = utils.create_answer(self.answer_content, self.user1, q)
        self.client.login(self.username2, self.password)
        # act
        res = self.client.delete_answer(self.question.pk, a.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer.pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))
