from unittest import mock

from bs4 import BeautifulSoup
from django.conf import settings

from articles.models import Article
from articles.tests.base import ArticlesApiTestCase
from common.test_utils import assert_message_in_response
from forum import models
from forum.views import notifications


class TestAddArticle(ArticlesApiTestCase):
    title = "my_question_title"
    question_content = "my_question_content"
    tags = [
        "my_first_tag",
    ]

    def test_create_article_get__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.add_article_get()
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("input", {"id": "tagsEdit"})))
        self.assertEqual(1, len(soup.find_all("textarea", {"id": "articleeditor"})))
        self.assertEqual(1, len(soup.find_all("input", {"name": "title"})))

    def test_post_question__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)

        models.Tag.objects.create(tag_word="tag1question")
        title = "question title with minimum acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "Article draft posted successfully")
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        notifications.notify_tag_followers_new_question.assert_called_once_with(self.users[0], set(tags), mock.ANY)
        self.assertEqual(len(tags), notifications.notify_tag_followers_new_question.call_count)

    # TODO fix
    # @mock.patch('forum.jobs.start_job')
    # def test_post_question__with_invites__green(self, start_job: mock.MagicMock):
    #     # arrange
    #     self.client.login(self.usernames[0], self.password)
    #
    #     tag = models.Tag.objects.create(tag_word='tag1question')
    #     title = 'article title with minimum acceptable chars'
    #     content = 'question content with more than minimum chars'
    #     tags = [tag.tag_word, ]
    #     # act
    #     res = self.client.add_article_post(title, content,
    #                                        tags=', '.join(tags),
    #                                        invites=','.join(self.usernames[1:]))
    #     # assert
    #     qs = models.Question.objects.filter(title=title, content=content)
    #     self.assertEqual(1, qs.count())
    #     q = qs.first()
    #     tags_list = list(q.tags.all())
    #     self.assertEqual(len(tags_list), len(tags))
    #     assert_message_in_response(res, 'Article draft posted successfully')
    #     subject_line = f'{self.usernames[0]} invited you to answer a question'
    #     calls = [
    #         mock.call(jobs.notify_user_email, self.users[2], subject_line, mock.ANY, mock.ANY, True),
    #         mock.call(jobs.notify_user_email, self.users[1], subject_line, mock.ANY, mock.ANY, True),
    #     ]
    #     start_job.assert_has_calls(calls, any_order=True)

    def test_post_question__short_title__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "short"
        content = "question content with more than minimum chars"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(res, "Error: Title has 5 characters, must be between 10 and 255 characters.")
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__short_content__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "title with sufficient length"
        content = "short"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(
            res,
            "Error: Content length is 5 characters, should be between 10 and 200 characters",
        )
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__long_content__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "title with sufficient length"
        content = "long content: " + "x" * settings.MAX_ARTICLE_CONTENT_LENGTH
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(
            res,
            "Error: Content length is 214 characters, should be between 10 and 200 characters",
        )
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__long_title__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "x" * 300
        content = "question content with more than minimum chars"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(
            res,
            "Error: Title has 300 characters, must be between 10 and 255 characters.",
        )
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__empty_tag__should_not_be_added(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "article title with minimum acceptable chars"
        content = "question content with more than minimum chars"
        tags = ["tag1", "  ", "tag2"]
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags))
        # assert
        qs = Article.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(t.tag_word for t in q.tags.all())
        self.assertEqual(2, len(tags_list))
        for tag in ["tag1", "tag2"]:
            assert tag in tags_list, f"expected {tag} in {tags_list} but is not there"
        assert_message_in_response(res, "Article draft posted successfully")

    def test_post_question__with_answer_flag_off__should_create_answer(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "article title with minimum acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = "answer content for question with answer"
        # act
        res = self.client.add_article_post(title, content, ", ".join(tags), answereditor=answer_content)
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertFalse(q.has_accepted_answer)
        self.assertEqual(0, q.answer_set.count())
        notifications.notify_tag_followers_new_question.assert_called_once_with(self.users[0], set(tags), mock.ANY)
        assert_message_in_response(res, "Article draft posted successfully")
        self.assertEqual(len(tags), notifications.notify_tag_followers_new_question.call_count)
