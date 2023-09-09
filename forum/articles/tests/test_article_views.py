from unittest import mock

from bs4 import BeautifulSoup
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse

from articles.tests.base import ArticlesApiTestCase
from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from common.test_utils import assert_url_in_chain
from forum import models, jobs
from forum.integrations import slack_api
from forum.jobs import add_meilisearch_document
from forum.models import QuestionInviteToAnswer
from forum.views import utils, notifications
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks


class TestArticleDetailView(ArticlesApiTestCase):
    title = 'my_question_title'
    content = 'my_question_content'
    tags = ['my_first_tag', ]
    answer_content = 'answer------content'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.article = utils.create_question(cls.users[1], cls.title, cls.content, ','.join(cls.tags), type=Question.POST_TYPE_ARTICLE)
        settings.MAX_COMMENTS = 3

    def test_articles_detail_view__user_not_logged_in(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_article_detail_get(self.article.pk)
        # assert
        self.assertEqual(200, res.status_code)

    def test_articles_detail_view__non_existing_question(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_article_detail_get(self.article.pk + 1)
        # assert
        self.assertEqual(404, res.status_code)

    def test_articles_detail_view__green(self):
        self.client.login(self.usernames[0], self.password)
        utils.create_answer(self.answer_content, self.users[0], self.article)
        # act
        res = self.client.view_article_detail_get(self.article.pk, )
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')  # noqa: F841
        # todo

    def test_articles_detail_view__inactive_user__green(self):
        self.client.login(self.usernames[0], self.password)
        utils.create_answer(self.answer_content, self.users[1], self.article)
        self.users[1].is_active = False
        self.users[1].save()
        # act
        res = self.client.view_article_detail_get(self.article.pk, )
        # assert
        self.assertContains(res, 'Inactive User', status_code=200)

    def test_articles_detail_view__calling_background_task(self):
        self.client.login(self.usernames[0], self.password)
        prev_views = self.article.views
        settings.RUN_ASYNC_JOBS_SYNC = True
        # act
        res = self.client.view_article_detail_get(self.article.pk, )
        res = self.client.view_article_detail_get(self.article.pk, )
        # cleanup
        settings.RUN_ASYNC_JOBS_SYNC = False
        # assert
        self.article.refresh_from_db()
        self.assertEqual(200, res.status_code)
        self.assertEqual(prev_views + 1, self.article.views)

    def test_articles_detail_view__calling_background_task_with_author__does_not_increase_views(self):
        self.client.login(self.usernames[1], self.password)
        self.article.refresh_from_db()
        prev_views = self.article.views
        settings.RUN_ASYNC_JOBS_SYNC = True
        # act
        res = self.client.view_article_detail_get(self.article.pk)
        res = self.client.view_article_detail_get(self.article.pk)
        # cleanup
        settings.RUN_ASYNC_JOBS_SYNC = False
        # assert
        self.article.refresh_from_db()
        self.assertEqual(200, res.status_code)
        self.assertEqual(prev_views, self.article.views)

    def test_articles_detail_view_with_invites__show_question_invitees(self):
        # arrange
        QuestionInviteToAnswer.objects.create(
            question=self.article,
            inviter=self.users[0],
            invitee=self.users[1],
        )
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_article_detail_get(self.article.pk)
        res2 = self.client.view_partial_question_invites_get(self.article.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(200, res2.status_code)
        self.assertContains(res2, 'People asked')
        self.assertContains(res2, self.usernames[1])

    @mock.patch('forum.jobs.start_job')
    def test_articles_detail_view_create_question_comment_green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = 'comment------content'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.article).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.article.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.article.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
        ], any_order=True)
        self.article.refresh_from_db()
        self.assertEqual(comment.created_at, self.article.last_activity)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_articles_detail_view_create_question_comment__with_mention__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.article).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.article.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.article.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(jobs.notify_user_email, self.users[1],
                      f'{self.users[0].display_name()} mentioned you in a comment',
                      mock.ANY, mock.ANY, False
                      ),
            mock.call(view_thread_background_tasks, self.users[0], self.article),
            mock.call(add_meilisearch_document, self.article.id),
        ], any_order=True)
        self.assertEqual(5, start_job.call_count)
        self.article.refresh_from_db()
        self.assertEqual(comment.created_at, self.article.last_activity)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_articles_detail_view_create_question_comment__with_mention_user_does_not_exists__should_not_notify(
            self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}xx'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.article).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.article.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.article.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(view_thread_background_tasks, self.users[0], self.article),
            mock.call(add_meilisearch_document, self.article.id),
        ], any_order=True)
        self.assertEqual(4, start_job.call_count)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_articles_detail_view_create_question_comment__with_mention_user_bad_quotes__should_handle_bad_quotes(
            self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}xx "quote'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.article).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.article.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.article.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(view_thread_background_tasks, self.users[0], self.article),
            mock.call(add_meilisearch_document, self.article.id),
        ], any_order=True)
        self.assertEqual(4, start_job.call_count)

    def test_articles_detail_view_create_question_comment__bad_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = '***comment------content***'
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk + 1, comment_content)
        # assert
        comment_count = models.QuestionComment.objects.filter(question_id=self.article.pk + 1).count()
        self.assertEqual(0, comment_count)
        self.assertNotContains(res, comment_content)

    def test_articles_detail_view_create_answer__bad_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        jobs.start_job = mock.MagicMock()
        # act
        res = self.client.thread_add_answer(self.article.pk + 1, answer_content)
        # assert
        answer_count = models.Answer.objects.filter(question=self.article).count()
        self.assertEqual(0, answer_count)
        assert_url_in_chain(res, reverse('forum:list'))
        jobs.start_job.assert_not_called()

    def test_articles_detail_view_unknown_post_action(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.thread_unknown_post_action(self.article.pk, )
        # assert
        assert_url_in_chain(res, reverse('forum:thread', args=[self.article.pk, ]))

    def test_articles_detail_views_dont_change__when_same_user_viewed(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.view_article_detail_get(self.article.pk)
        # assert
        self.assertEqual(200, res.status_code)
        q = models.Question.objects.get(pk=self.article.pk)
        self.assertEqual(0, q.views)

    def test_thread_max_answers_in_question__add_answer__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        for _ in range(settings.MAX_ANSWERS):
            utils.create_answer(answer_content, self.users[0], self.article)
        new_answer_content = 'new---answer------content---'
        # act
        res = self.client.thread_add_answer(self.article.pk, new_answer_content)
        # assert
        self.assertNotContains(res, new_answer_content)

    def test_articles_detail_view_create_question_comment__empty_comment_should_not_add(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = '   '
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionComment.objects.filter(question=self.article).count())

    def test_articles_detail_view_create_answer_empty_content__should_not_add(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = '     '
        # act
        res = self.client.thread_add_answer(self.article.pk, answer_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.Answer.objects.filter(question=self.article).count())

    def test_articles_detail_view_create_question_comment__max_comments_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = 'comment------content'
        another_comment_content = 'comment------content$$%%@@##'
        for _ in range(settings.MAX_COMMENTS):
            self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, comment_content)
        # act
        res = self.client.thread_add_comment(self.article.pk, 'question', self.article.pk, another_comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(settings.MAX_COMMENTS, models.QuestionComment.objects.filter(question=self.article).count())
        comment_list = list(models.QuestionComment.objects.filter(question=self.article))
        for c in comment_list:
            self.assertEqual(comment_content, c.content)

    def test_articles_detail_view_create_question_comment__non_existing_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        a = utils.create_answer(answer_content, self.users[0], self.article)
        comment_content = 'comment------content'
        # act
        res = self.client.thread_add_comment(self.article.pk, 'answer', a.pk + 6, comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.AnswerComment.objects.all().count())

    def test_articles_detail_view__links_should_have_target_attribute(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = '[link](http://example.com)'
        utils.create_answer(answer_content, self.users[0], self.article)
        # act
        res = self.client.view_article_detail_get(self.article.pk)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        answer_div = soup.find_all('div', {'class': 'user-content'})[0]
        ahref_list = answer_div.find_all('a')
        for ahref in ahref_list:
            self.assertEqual('_blank', ahref.attrs.get('target'))


class TestForumArticleListView(ArticlesApiTestCase):
    title = 'my_article_title'
    content = 'my_article_content'
    tags = ['my_first_tag', 'my_second_tag']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        for i in range(settings.QUESTIONS_PER_PAGE + 2):
            utils.create_question(cls.users[0], cls.title, cls.content, ','.join(cls.tags), type=Question.POST_TYPE_ARTICLE, )

    def test_articles_list__empty_list_user_not_loggedin_default_tab(self):
        # act
        res = self.client.articles_list()
        # assert
        self.assertContains(res, 'Login')
        assert_url_in_chain(res, reverse('userauth:login') + '?next=' + reverse('articles:list'))

    def test_articles_list__empty_list_user_loggedin_default_tab(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list()
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertNotContains(res, 'Login')

    def test_articles_list__user_loggedin_default_tab(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list()
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertContains(res, 'Ask Question')
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.content)

    def test_articles_list__latest_tab(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list(tab='latest')
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertContains(res, 'Ask Question')
        self.assertContains(res, self.title)
        soup = BeautifulSoup(res.content, 'html.parser')
        assert 'active' in soup.find(text='Latest').parent.parent.get('class')
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.content)

    def test_articles_list__most_viewed_tab(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list(tab='mostviewed')
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertContains(res, 'Ask Question')
        self.assertContains(res, self.title)

        soup = BeautifulSoup(res.content, 'html.parser')
        assert 'active' in soup.find(text='Most viewed').parent.parent.get('class')
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.content)

    def test_articles_list__non_existing_page(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list(page=20)
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertContains(res, 'Ask Question')
        self.assertContains(res, '<span class="page-link">2 <span class="sr-only">(current)</span></span>')
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.content)

    def test_articles_list__existing_page(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.articles_list(page=2)
        # assert
        self.assertContains(res, 'All articles')
        self.assertContains(res, 'Propose article')
        self.assertContains(res, 'Ask Question')
        self.assertContains(res, '<span class="page-link">2 <span class="sr-only">(current)</span></span>', html=True)
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.content)
