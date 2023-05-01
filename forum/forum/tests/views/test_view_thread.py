from unittest import mock

from bs4 import BeautifulSoup
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from common.test_utils import assert_url_in_chain
from forum import models, jobs
from forum.integrations import slack_api
from forum.jobs import add_meilisearch_document
from forum.models import QuestionInviteToAnswer, TagFollow
from forum.tests.base import ForumApiTestCase
from forum.views import utils, notifications
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from userauth.models import ForumUser


class TestThreadView(ForumApiTestCase):
    title = 'my_question_title'
    content = 'my_question_content'
    tags = ['my_first_tag', ]
    answer_content = 'answer------content'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[0], cls.title, cls.content, ','.join(cls.tags))
        settings.MAX_ANSWERS = 3
        settings.MAX_COMMENTS = 3

    def test_thread_view__user_not_logged_in(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_thread_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)

    def test_thread_view__non_existing_question(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_thread_get(self.question.pk + 1)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('forum:list'))

    def test_thread_view__order_by_latest__green(self):
        self.client.login(self.usernames[0], self.password)
        utils.create_answer(self.answer_content, self.users[0], self.question)
        # act
        res = self.client.view_thread_get(self.question.pk, order_by='latest')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        assert 'active' in soup.find(text='Latest').parent.parent.get('class')

    def test_thread_view__inactive_user__green(self):
        self.client.login(self.usernames[0], self.password)
        utils.create_answer(self.answer_content, self.users[1], self.question)
        self.users[1].is_active = False
        self.users[1].save()
        # act
        res = self.client.view_thread_get(self.question.pk, order_by='latest')
        # assert
        self.assertContains(res, 'Inactive User', status_code=200)

    @mock.patch('forum.jobs.start_job')
    def test_thread_view__calling_background_task(self, start_job: mock.MagicMock):
        self.client.login(self.usernames[2], self.password)
        prev_views = self.question.views
        # act
        res = self.client.view_thread_get(self.question.pk, order_by='latest')
        # assert
        self.assertEqual(200, res.status_code)

        start_job.assert_has_calls([
            mock.call(view_thread_background_tasks, self.users[2], self.question),
        ], any_order=True)
        # act 2
        view_thread_background_tasks(self.users[2], self.question)
        self.assertEqual(prev_views + 1, self.question.views)

    @mock.patch('forum.jobs.start_job')
    def test_thread_view__calling_background_task_with_author__does_not_increase_views(self, start_job: mock.MagicMock):
        self.client.login(self.question.author.username, self.password)
        self.question.refresh_from_db()
        prev_views = self.question.views
        # act
        res = self.client.view_thread_get(self.question.pk, order_by='latest')
        # cleanup
        # assert
        self.assertEqual(200, res.status_code)
        start_job.assert_has_calls([
            mock.call(view_thread_background_tasks, self.question.author, self.question),
        ], any_order=True)
        view_thread_background_tasks(self.question.author, self.question)
        self.question.refresh_from_db()
        self.assertEqual(prev_views, self.question.views)

    def test_thread_view__order_by_oldest__green(self):
        self.client.login(self.usernames[0], self.password)
        utils.create_answer(self.answer_content, self.users[0], self.question)
        # act
        res = self.client.view_thread_get(self.question.pk, order_by='oldest')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        assert 'active' in soup.find(text='Oldest').parent.parent.get('class')

    def test_thread_view_with_invites__show_question_invitees(self):
        # arrange
        QuestionInviteToAnswer.objects.create(
            question=self.question,
            inviter=self.users[0],
            invitee=self.users[1],
        )
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_thread_get(self.question.pk)
        res2 = self.client.view_partial_question_invites_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(200, res2.status_code)
        self.assertContains(res2, 'People asked')
        self.assertContains(res2, self.usernames[1])

    def test_thread_view_with_invites__has_accepted_answer__dont_show_question_invitees(self):
        # arrange
        self.question.has_accepted_answer = True
        self.question.save()
        QuestionInviteToAnswer.objects.create(
            question=self.question,
            inviter=self.users[0],
            invitee=self.users[1],
        )
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_thread_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertNotContains(res, self.usernames[1])
        self.assertNotContains(res, 'People asked')

    def test_thread_view_anonymous_question__should_not_show_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        q = utils.create_question(self.users[0], self.title, self.content, ','.join(self.tags), is_anonymous=True)
        # act
        res = self.client.view_thread_get(q.pk)
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('img', {'src': "/media/default_pics/anonymous.png"})))
        self.assertEqual(0, len(soup.find_all(text=self.usernames[0])))

    @mock.patch('forum.jobs.start_job')
    def test_thread_view_create_question_comment_green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = 'comment------content'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.question).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.question.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.question.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
        ], any_order=True)
        self.question.refresh_from_db()
        self.assertEqual(comment.created_at, self.question.last_activity)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_thread_view_create_question_comment__with_mention__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.question).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.question.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.question.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(jobs.notify_user_email, self.users[1],
                      f'{self.users[0].display_name()} mentioned you in a comment',
                      mock.ANY, mock.ANY, False
                      ),
            mock.call(view_thread_background_tasks, self.users[0], self.question),
            mock.call(add_meilisearch_document, self.question.id),
        ], any_order=True)
        self.assertEqual(5, start_job.call_count)
        self.question.refresh_from_db()
        self.assertEqual(comment.created_at, self.question.last_activity)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_thread_view_create_question_comment__with_mention_user_does_not_exists__should_not_notify(
            self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}xx'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.question).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.question.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.question.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(view_thread_background_tasks, self.users[0], self.question),
            mock.call(add_meilisearch_document, self.question.id),
        ], any_order=True)
        self.assertEqual(4, start_job.call_count)

    @override_settings(MEILISEARCH_ENABLED=False)
    @mock.patch('forum.jobs.start_job')
    def test_thread_view_create_question_comment__with_mention_user_bad_quotes__should_handle_bad_quotes(
            self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = f'comment mentions @{self.usernames[1]}xx "quote'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        comment = models.QuestionComment.objects.filter(question=self.question).first()
        self.assertEqual(comment_content, comment.content)
        self.assertEqual(self.users[0], comment.author)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.question.pk}/comments"})))
        notifications._notify_question_followers.assert_called_once()
        start_job.assert_has_calls([
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.question.author.email),
            mock.call(review_bagdes_event, TRIGGER_EVENT_TYPES['Create comment']),
            mock.call(view_thread_background_tasks, self.users[0], self.question),
            mock.call(add_meilisearch_document, self.question.id),
        ], any_order=True)
        self.assertEqual(4, start_job.call_count)

    @mock.patch('forum.jobs.start_job')
    def test_thread_view_create_answer_comment__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)
        a = models.Answer.objects.create(content=self.answer_content, author=self.users[0], question=self.question)
        comment_content = 'comment------content'
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'answer', a.pk, comment_content)
        # assert
        self.assertEqual(1, models.AnswerComment.objects.filter(answer=a).count())
        comment = models.AnswerComment.objects.filter(answer=a).first()
        self.assertEqual(comment_content, comment.content)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/question/{self.question.pk}/comments"})))
        self.assertEqual(1, len(soup.find_all('div', {'hx-get': f"/answer/{a.pk}/comments"})))
        notifications._notify_question_followers.assert_not_called()
        start_job.assert_has_calls([
            mock.call(jobs.notify_user_email, a.author, mock.ANY, mock.ANY, mock.ANY, False),
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.question.author.email),
        ])
        self.question.refresh_from_db()
        self.assertEqual(comment.created_at, self.question.last_activity)

    def test_thread_view_create_question_comment__empty_comment__should_not_create(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = ' ' * settings.MIN_COMMENT_LENGTH
        notifications._notify_question_followers = mock.MagicMock()
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionComment.objects.filter(question=self.question).count())

    def test_thread_view_create_question_comment__bad_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = '***comment------content***'
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk + 1, comment_content)
        # assert
        comment_count = models.QuestionComment.objects.filter(question_id=self.question.pk + 1).count()
        self.assertEqual(0, comment_count)
        self.assertNotContains(res, comment_content)

    def test_thread_view_create_answer_green(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        answer_content = 'answer------content'
        notifications._notify_question_followers = mock.MagicMock()
        jobs.start_job = mock.MagicMock()
        # act
        res = self.client.thread_add_answer(self.question.pk, answer_content)
        # assert
        answer = models.Answer.objects.filter(question=self.question).first()
        self.assertEqual(answer_content, answer.content)
        self.assertEqual(self.users[1], answer.author)
        self.assertContains(res, answer_content)
        self.assertEqual(len(self.question.tags.all()), TagFollow.objects.filter(user=self.users[1]).count())
        notifications._notify_question_followers.assert_called_once()
        jobs.start_job.assert_has_calls([
            mock.call(jobs.update_tag_follow_stats, answer),
            mock.call(slack_api.slack_post_im_message_to_email, mock.ANY, self.users[0].email),
        ])
        self.question.refresh_from_db()
        self.assertEqual(answer.updated_at, self.question.last_activity)

    def test_thread_view_create_answer__bad_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        jobs.start_job = mock.MagicMock()
        # act
        res = self.client.thread_add_answer(self.question.pk + 1, answer_content)
        # assert
        answer_count = models.Answer.objects.filter(question=self.question).count()
        self.assertEqual(0, answer_count)
        assert_url_in_chain(res, reverse('forum:list'))
        jobs.start_job.assert_not_called()

    def test_thread_view_unknown_post_action(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.thread_unknown_post_action(self.question.pk, )
        # assert
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.pk, ]))

    def test_thread_max_answers_in_question__no_new_answer_editor(self):
        # arrange
        users = [ForumUser.objects.create_user(username=f'{self.usernames[0]}{i}',
                                               password='1111',
                                               email=f'{self.usernames[0]}{i}@use.com'
                                               )
                 for i in range(settings.MAX_ANSWERS + 1)]
        q = utils.create_question(users[settings.MAX_ANSWERS], self.title, self.content, ','.join(self.tags))
        answer_content = 'answer------content'
        for i in range(settings.MAX_ANSWERS):
            utils.create_answer(answer_content, users[i], q)
        self.client.login(users[settings.MAX_ANSWERS].username, '1111')
        # act
        res = self.client.view_thread_get(q.pk)
        # assert
        self.assertNotContains(res, '<textarea id="editor1" name="editor1"></textarea>')
        self.assertContains(res, 'Too many answers, please edit previous answers')

    def test_thread_max_answers_in_question__create_answer__should_fail(self):
        # arrange
        users = [ForumUser.objects.create_user(username=f'{self.usernames[0]}{i}',
                                               password='1111',
                                               email=f'{self.usernames[0]}{i}@use.com'
                                               )
                 for i in range(settings.MAX_ANSWERS + 1)]
        answer_content = 'answer------content'
        for i in range(settings.MAX_ANSWERS):
            utils.create_answer(answer_content, users[i], self.question)
        new_answer_content = 'new---answer------content---'
        self.client.login(users[settings.MAX_ANSWERS].username, '1111')
        # act
        res = self.client.thread_add_answer(self.question.pk, new_answer_content)
        # assert
        self.assertNotContains(res, new_answer_content)

    @mock.patch('forum.jobs.start_job')
    def test_thread_views_increase__when_different_user_viewed(self, start_job: mock.MagicMock):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.view_thread_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        start_job.assert_called_once_with(view_thread_background_tasks, self.users[1], self.question)
        view_thread_background_tasks(self.users[1], self.question)
        self.question.refresh_from_db()
        self.assertEqual(1, self.question.views)

    def test_thread_views_dont_change__when_same_user_viewed(self):
        self.client.login(self.question.author.username, self.password)
        # act
        res = self.client.view_thread_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        q = models.Question.objects.get(pk=self.question.pk)
        self.assertEqual(0, q.views)

    def test_thread_max_answers_in_question__add_answer__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        for _ in range(settings.MAX_ANSWERS):
            utils.create_answer(answer_content, self.users[0], self.question)
        new_answer_content = 'new---answer------content---'
        # act
        res = self.client.thread_add_answer(self.question.pk, new_answer_content)
        # assert
        self.assertNotContains(res, new_answer_content)

    def test_thread_view_create_question_comment__empty_comment_should_not_add(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = '   '
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionComment.objects.filter(question=self.question).count())

    def test_thread_view_create_answer_empty_content__should_not_add(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = '     '
        # act
        res = self.client.thread_add_answer(self.question.pk, answer_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.Answer.objects.filter(question=self.question).count())

    def test_thread_view_create_question_comment__max_comments_reached(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        comment_content = 'comment------content'
        another_comment_content = 'comment------content$$%%@@##'
        for _ in range(settings.MAX_COMMENTS):
            self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, comment_content)
        # act
        res = self.client.thread_add_comment(self.question.pk, 'question', self.question.pk, another_comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(settings.MAX_COMMENTS, models.QuestionComment.objects.filter(question=self.question).count())
        comment_list = list(models.QuestionComment.objects.filter(question=self.question))
        for c in comment_list:
            self.assertEqual(comment_content, c.content)

    def test_thread_view_create_question_comment__non_existing_question(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = 'answer------content'
        a = utils.create_answer(answer_content, self.users[0], self.question)
        comment_content = 'comment------content'
        # act
        res = self.client.thread_add_comment(self.question.pk, 'answer', a.pk + 6, comment_content)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.AnswerComment.objects.all().count())

    def test_thread_view__links_should_have_target_attribute(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        answer_content = '[link](http://example.com)'
        utils.create_answer(answer_content, self.users[0], self.question)
        # act
        res = self.client.view_thread_get(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        answer_div = soup.find_all('div', {'class': 'user-content'})[0]
        ahref_list = answer_div.find_all('a')
        for ahref in ahref_list:
            self.assertEqual('_blank', ahref.attrs.get('target'))
