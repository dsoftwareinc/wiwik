import os
from unittest import mock

from bs4 import BeautifulSoup
from django.test.utils import override_settings
from django.urls import reverse

from badges.jobs import review_bagdes_event
from common.test_utils import assert_message_in_response, assert_url_in_chain
from forum import models, jobs
from forum.jobs import add_meilisearch_document
from forum.tests.base import ForumApiTestCase
from forum.views import utils
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from userauth.models import ForumUser


class TestEditQuestionView(ForumApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content_with more than 20 chars'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2 = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)
        cls.question = utils.create_question(cls.user1, cls.title, cls.question_content, ','.join(cls.tags))

    def test_edit_question_get__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_question_get(self.question.pk)
        # assert
        self.assertContains(res, 'input id="tagsEdit" name="tags"')
        self.assertContains(res, f'<textarea id="queseditor" name="queseditor">{self.question_content}')
        self.assertContains(res, f'<textarea name="title" style="width:100%">{self.title}')

    def test_edit_question_get__not_author__should_not_allow(self):
        # arrange
        self.client.login(self.username2, self.password)
        # act
        res = self.client.edit_question_get(self.question.pk)
        # assert
        assert_message_in_response(res, 'You can not edit this question')
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    @mock.patch('forum.jobs.start_job')
    def test_edit_question_post__author_edit__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.username1, self.password)
        new_title = 'new_title_with_appropriate_length'
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_question_post(self.question.pk,
                                             new_title,
                                             new_content,
                                             ','.join(new_tags))
        # assert
        q = models.Question.objects.get(pk=self.question.pk)
        self.assertEqual(new_title, q.title)
        self.assertEqual(new_content, q.content)
        self.assertEqual(set(new_tags), set(q.tag_words()))
        assert_message_in_response(res, 'Question updated successfully')
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))
        start_job.assert_has_calls([
            mock.call(jobs.update_tag_follow_stats, q.id, q.author_id),
        ])  # No notification should be sent if author edited.

    def test_edit_question_post__no_changes(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_question_post(self.question.pk,
                                             self.title,
                                             self.question_content,
                                             ','.join(self.tags))
        # assert
        assert_message_in_response(res, 'Question updated successfully')
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_edit_question_post__edit_by_other_user__green(self, start_job: mock.MagicMock):
        # arrange
        admin_user = ForumUser.objects.create_superuser('admin', 'a@a.com', '1111')
        self.client.login('admin', '1111')
        new_title = 'new_title_with_appropriate_length'
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_question_post(self.question.pk,
                                             new_title,
                                             new_content,
                                             ','.join(new_tags) + ', ')
        # assert
        q = models.Question.objects.get(pk=self.question.pk)
        self.assertEqual(new_title, q.title)
        self.assertEqual(new_content, q.content)
        self.assertEqual(set(new_tags), set(q.tag_words()))
        self.assertEqual(admin_user, q.editor)
        assert_message_in_response(res, 'Question updated successfully')
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk]))
        votes_list = list(models.VoteActivity.objects.all())
        self.assertEqual(1, len(votes_list))
        self.assertEqual(2, votes_list[0].reputation_change)
        self.assertEqual(admin_user, votes_list[0].target)
        self.assertEqual(q, votes_list[0].question)
        admin_user.refresh_from_db()
        self.assertEqual(2, admin_user.reputation_score)
        start_job.assert_has_calls([
            mock.call(jobs.update_tag_follow_stats, q.id, q.author_id),
            mock.call(add_meilisearch_document, q.id),
            mock.call(jobs.notify_user_email, q.author, mock.ANY, mock.ANY, mock.ANY, False),
            mock.call(review_bagdes_event, mock.ANY),
            mock.call(view_thread_background_tasks, admin_user, q),
        ])

    def test_edit_question_post__title_exceed_max_length__should_fail(self):
        # arrange
        self.client.login(self.username1, self.password)
        max_length = int(os.getenv('MAX_QUESTION_TITLE_LENGTH', 30000))
        new_title = 'new_title_with_appropriate_length' + 'x' * max_length
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_question_post(self.question.pk,
                                             new_title,
                                             new_content,
                                             ','.join(new_tags))
        # assert
        q = models.Question.objects.get(pk=self.question.pk)
        assert_message_in_response(res, 'Error: Title too long')
        self.assertEqual(self.question_content, q.content)
        self.assertEqual(set(self.tags), set(q.tag_words()))
        self.assertEqual(0, len(res.redirect_chain))
        # test for #302
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(','.join(new_tags), soup.find('input', {'id': 'tagsEdit'}).attrs['value'])

    def test_edit_question_get__not_existing_question__return_not_found(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_question_get(self.question.pk + 5)
        # assert
        self.assertEqual(404, res.status_code)
