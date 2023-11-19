from unittest import mock

from django.urls import reverse

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from common.test_utils import assert_message_in_response, assert_url_in_chain
from forum import models, jobs
from forum.integrations import slack_api
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from userauth.models import ForumUser


class TestEditAnswerView(ForumApiTestCase):


    @classmethod
    def setUpClass(cls):
        super().setUpClass()        
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))
        cls.answer = utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        cls.answer_url = reverse('forum:thread', args=[cls.question.pk]) + f'#answer_{cls.answer.pk}'
        cls.previous_last_activity = cls.question.last_activity

    def test_edit_answer_get__green(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.edit_answer_get(self.answer.pk)
        # assert
        self.assertContains(res, f'<textarea id="queseditor" name="queseditor">{self.answer_content}')
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, self.previous_last_activity)

    def test_edit_answer_get__no_permissions__should_not_allow(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.edit_answer_get(self.answer.pk)
        # assert
        assert_message_in_response(res, 'You can not edit this answer')
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    @mock.patch('forum.jobs.start_job')
    def test_edit_answer_post__author_edit__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[1], self.password)
        new_content = 'new content with good enough length'
        # act
        res = self.client.edit_answer_post(self.answer.pk, new_content)
        # assert
        self.answer.refresh_from_db()
        self.assertEqual(new_content, self.answer.content)
        assert_message_in_response(res, 'Answer updated successfully')
        assert_url_in_chain(res, self.answer_url)
        start_job.assert_has_calls([
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Update post']),
            mock.call(view_thread_background_tasks, self.users[1], self.answer.question),
        ], any_order=True)  # no notification should be sent.
        self.question.refresh_from_db()
        self.assertEqual(self.answer.updated_at, self.question.last_activity)
        self.assertGreater(self.question.last_activity, self.previous_last_activity)

    def test_edit_answer_post__no_changes(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        self.answer.refresh_from_db()
        # act
        res = self.client.edit_answer_post(self.answer.pk, self.answer.content)
        # assert
        assert_message_in_response(res, 'Answer updated successfully')
        assert_url_in_chain(res, self.answer_url)
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, self.previous_last_activity)

    @mock.patch('forum.jobs.start_job')
    def test_edit_answer_post__edit_by_other_user__green(self, start_job: mock.MagicMock):
        # arrange
        admin_user = ForumUser.objects.create_superuser('admin', 'a@a.com', '1111')
        self.client.login('admin', '1111')
        new_content = 'new content with good enough length'
        # act
        res = self.client.edit_answer_post(self.answer.pk, new_content)
        # assert
        self.answer.refresh_from_db()
        self.assertEqual(new_content, self.answer.content)
        self.assertEqual(admin_user, self.answer.editor)
        assert_message_in_response(res, 'Answer updated successfully')
        assert_url_in_chain(res, self.answer_url)
        votes_list = list(models.VoteActivity.objects.all())
        self.assertEqual(1, len(votes_list))
        self.assertEqual(2, votes_list[0].reputation_change)
        self.assertEqual(admin_user, votes_list[0].target)
        self.assertEqual(self.question, votes_list[0].question)
        self.assertEqual(self.answer, votes_list[0].answer)
        admin_user.refresh_from_db()
        self.assertEqual(2, admin_user.reputation_score)
        start_job.assert_has_calls([
            mock.call(jobs.notify_user_email, self.answer.author, mock.ANY, mock.ANY, mock.ANY, False),
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.answer.author.email),
        ])
        self.question.refresh_from_db()
        self.assertGreater(self.question.last_activity, self.previous_last_activity)

    def test_edit_answer_post__empty_content__should_not_update(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.edit_answer_post(self.answer.pk, '')
        # assert
        self.answer.refresh_from_db()
        assert_message_in_response(res, 'Can not erase answer content')
        assert_url_in_chain(res, self.answer_url)
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, self.previous_last_activity)

    def test_edit_answer_get__not_existing_answer__return_not_found(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.edit_answer_get(self.answer.pk + 5)
        # assert
        self.assertEqual(404, res.status_code)
        self.question.refresh_from_db()
        self.assertEqual(self.question.last_activity, self.previous_last_activity)
