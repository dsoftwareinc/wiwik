from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestDeleteQuestionView(ForumApiTestCase):
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))
        utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        utils.create_answer(cls.answer_content, cls.users[0], cls.question)
        a = utils.create_answer(cls.answer_content, cls.users[2], cls.question)
        cls.answer_pk = a.pk

    def test_get_delete_question_confirmation_page__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.get_delete_question_confirmation_page(self.question.pk)
        # assert
        self.assertEqual(1, models.Question.objects.all().count())
        self.assertEqual(3, models.Answer.objects.all().count())
        self.assertEqual(f'/question/{self.question.pk}/delete', res.request['PATH_INFO'])

    def test_delete_question__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer = models.Answer.objects.get(pk=self.answer_pk)
        utils.upvote(self.users[0], answer)
        utils.upvote(self.users[1], answer)
        utils.upvote(self.users[1], self.question)
        utils.upvote(self.users[2], self.question)
        question_user_previous_reputation = self.question.author.reputation_score
        answer_user_previous_reputation = answer.author.reputation_score
        # act
        res = self.client.delete_question(self.question.pk)
        # assert
        self.assertEqual(0, models.Question.objects.all().count())
        self.assertEqual(0, models.Answer.objects.all().count())
        self.users[0].refresh_from_db()
        self.users[2].refresh_from_db()
        self.assertEqual(question_user_previous_reputation - 20, self.users[0].reputation_score)
        self.assertEqual(answer_user_previous_reputation - 20, self.users[2].reputation_score)
        assert_url_in_chain(res, reverse('forum:list'))

    def test_delete_question__user_not_logged_in(self):
        # arrange
        # act
        res = self.client.delete_question(self.question.pk)
        # assert
        self.assertEqual(1, models.Answer.objects.filter(pk=self.answer_pk).count())
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' +
                            reverse('forum:question_delete', args=[self.question.pk, ]))

    def test_delete_question__question_owned_by_different_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_question(self.question.pk)
        # assert
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    def test_delete_question__question_does_not_exist(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_question(self.question.pk + 5)
        # assert
        self.assertEqual(3, models.Question.objects.get(pk=self.question.pk).answer_set.count())
        assert_url_in_chain(res, reverse('forum:list'))

    def test_delete_question__question_has_invites__should_delete_invites(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        self.client.invite_to_question_post(self.question.pk, ','.join([self.usernames[2], ]))
        pk = self.question.pk
        # act
        res = self.client.delete_question(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionInviteToAnswer.objects.all().count())
        self.assertEqual(0, models.Question.objects.filter(pk=pk).count())
