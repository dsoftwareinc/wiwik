import os
from unittest import mock

from bs4 import BeautifulSoup
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse

from articles.tests.base import ArticlesApiTestCase
from badges.jobs import review_bagdes_event
from common.test_utils import assert_message_in_response, assert_url_in_chain
from forum import models, jobs
from forum.jobs import add_meilisearch_document
from forum.views import utils
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from userauth.models import ForumUser


class TestEditArticleView(ArticlesApiTestCase):
    username1 = 'myusername1'
    username2 = 'myusername2'
    username3 = 'myusername3'
    password = 'magicalPa$$w0rd'
    title = 'my_article title'
    article_content = 'my_article_content_with more than 20 chars'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1: ForumUser = ForumUser.objects.create_user(cls.username1, f'{cls.username1}@a.com', cls.password)
        cls.user2: ForumUser = ForumUser.objects.create_user(cls.username2, f'{cls.username2}@a.com', cls.password)
        cls.article = utils.create_article(cls.user1, cls.title, cls.article_content, ','.join(cls.tags))

    def test_edit_article_get__green(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_article_get(self.article.pk)
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('input', {'id': 'tagsEdit', 'name': 'tags'})))
        self.assertEqual(1, len(soup.find_all('textarea', {'id': 'articleeditor', 'name': 'articleeditor'})))
        self.assertEqual(1, len(soup.find_all('input', {'name': 'title'})))

    def test_edit_article_get__not_author__should_not_allow(self):
        # arrange
        self.client.login(self.username2, self.password)
        # act
        res = self.client.edit_article_get(self.article.pk)
        # assert
        assert_message_in_response(res, 'You can not edit this article')
        assert_url_in_chain(res, reverse('articles:detail', args=[self.article.pk]))

    @mock.patch('forum.jobs.start_job')
    def test_edit_article_post__author_edit__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.username1, self.password)
        new_title = 'new_title_with_appropriate_length'
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_article_post(self.article.pk,
                                            new_title,
                                            new_content,
                                            ','.join(new_tags))
        # assert
        self.article.refresh_from_db()
        self.assertEqual(new_title, self.article.title)
        self.assertEqual(new_content, self.article.content)
        self.assertEqual(set(new_tags), set(self.article.tag_words()))
        assert_message_in_response(res, 'Article updated successfully')
        assert_url_in_chain(res, reverse('articles:detail', args=[self.article.pk]))
        start_job.assert_has_calls([
            mock.call(jobs.update_user_tag_stats, self.article.id, self.user1.id),
        ])  # No notification should be sent if author edited.

    def test_edit_article_post__no_changes(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_article_post(self.article.pk,
                                            self.title,
                                            self.article_content,
                                            ','.join(self.tags))
        # assert
        assert_message_in_response(res, 'Article updated successfully')
        assert_url_in_chain(res, reverse('articles:detail', args=[self.article.pk]))

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_edit_article_post__edit_by_other_user__green(self, start_job: mock.MagicMock):
        # arrange
        admin_user = ForumUser.objects.create_superuser('admin', 'a@a.com', '1111')
        self.client.login('admin', '1111')
        new_title = 'new_title_with_appropriate_length'
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_article_post(self.article.pk,
                                            new_title,
                                            new_content,
                                            ','.join(new_tags) + ', ')
        # assert
        self.article.refresh_from_db()
        self.assertEqual(new_title, self.article.title)
        self.assertEqual(new_content, self.article.content)
        self.assertEqual(set(new_tags), set(self.article.tag_words()))
        self.assertEqual(admin_user, self.article.editor)
        assert_message_in_response(res, 'Article updated successfully')
        assert_url_in_chain(res, reverse('articles:detail', args=[self.article.pk]))
        votes_list = list(models.VoteActivity.objects.all())
        self.assertEqual(1, len(votes_list))
        self.assertEqual(2, votes_list[0].reputation_change)
        self.assertEqual(admin_user, votes_list[0].target)
        self.assertEqual(self.article, votes_list[0].question)
        admin_user.refresh_from_db()
        self.assertEqual(2, admin_user.reputation_score)
        start_job.assert_has_calls([
            mock.call(jobs.update_user_tag_stats, self.article.id, self.article.author_id),
            mock.call(add_meilisearch_document, self.article.id),
            mock.call(jobs.notify_user_email, self.article.author, mock.ANY, mock.ANY, mock.ANY, False),
            mock.call(review_bagdes_event, mock.ANY),
            mock.call(view_thread_background_tasks, admin_user, self.article),
        ])

    def test_edit_article_post__title_exceed_max_length__should_fail(self):
        # arrange
        self.client.login(self.username1, self.password)
        new_title = 'new_title_with_appropriate_length' + 'x' * 255
        new_content = 'new content with good enough length'
        new_tags = ['tag1', 'tag2']
        # act
        res = self.client.edit_article_post(self.article.pk,
                                            new_title,
                                            new_content,
                                            ','.join(new_tags))
        # assert
        self.article.refresh_from_db()
        assert_message_in_response(res, 'Error: Title has 288 characters, must be between 10 and 255 characters.')
        self.assertEqual(self.article_content, self.article.content)
        self.assertEqual(set(self.tags), set(self.article.tag_words()))
        self.assertEqual(0, len(res.redirect_chain))
        # test for #302
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(','.join(new_tags), soup.find('input', {'id': 'tagsEdit'}).attrs['value'])

    def test_edit_article_get__not_existing_question__return_not_found(self):
        # arrange
        self.client.login(self.username1, self.password)
        # act
        res = self.client.edit_article_get(self.article.pk + 5)
        # assert
        self.assertEqual(404, res.status_code)
