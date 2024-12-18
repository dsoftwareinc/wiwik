from unittest import mock

from bs4 import BeautifulSoup
from constance import config

from common.test_utils import assert_message_in_response
from forum import models, jobs
from forum.tests.base import ForumApiTestCase
from forum.views import notifications


class TestAddQuestion(ForumApiTestCase):
    def test_post_question_get__with_anonymous_allowed__green(self):
        # arrange
        config.ALLOW_ANONYMOUS_QUESTION = True
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.add_question_get()
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("input", {"id": "tagsEdit"})))
        self.assertEqual(1, len(soup.find_all("textarea", {"id": "queseditor"})))
        self.assertEqual(1, len(soup.find_all("textarea", {"name": "title"})))
        self.assertEqual(1, len(soup.find_all("input", {"type": "checkbox", "name": "anonymous"})))

    def test_post_question_get__with_anonymous_disabled__green(self):
        # arrange
        config.ALLOW_ANONYMOUS_QUESTION = False
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.add_question_get()
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("input", {"id": "tagsEdit"})))
        self.assertEqual(1, len(soup.find_all("textarea", {"id": "queseditor"})))
        self.assertEqual(1, len(soup.find_all("textarea", {"name": "title"})))
        self.assertEqual(0, len(soup.find_all("input", {"type": "checkbox", "name": "anonymous"})))

    def test_post_question__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)

        models.Tag.objects.create(tag_word="tag1question")
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        notifications.notify_tag_followers_new_question.assert_called_once_with(self.users[0], set(tags), mock.ANY)
        assert_message_in_response(res, "Question posted successfully")
        self.assertEqual(len(tags), notifications.notify_tag_followers_new_question.call_count)

    @mock.patch("forum.jobs.start_job")
    def test_post_question__with_invites__green(self, start_job: mock.MagicMock):
        # arrange
        self.client.login(self.usernames[0], self.password)

        tag = models.Tag.objects.create(tag_word="tag1question")
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            tag.tag_word,
        ]
        # act
        res = self.client.add_question_post(title, content, tags=", ".join(tags), invites=",".join(self.usernames[1:]))
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs.first()
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        assert_message_in_response(res, "Question posted successfully")
        subject_line = f"{self.usernames[0]} invited you to answer a question"
        calls = [
            mock.call(
                jobs.notify_user_email,
                self.users[2],
                subject_line,
                mock.ANY,
                mock.ANY,
                True,
            ),
            mock.call(
                jobs.notify_user_email,
                self.users[1],
                subject_line,
                mock.ANY,
                mock.ANY,
                True,
            ),
        ]
        start_job.assert_has_calls(calls, any_order=True)

    def test_post_question__anonymous__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        models.Tag.objects.create(tag_word="tag1question")
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags), anonymous="on")
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        assert qs.count() == 1
        q = qs[0]
        self.assertTrue(q.is_anonymous)
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        for t in tags_list:
            assert t.tag_word in tags, f"expected {t.tag_word} in {tags_list} but is not there"
        notifications.notify_tag_followers_new_question.assert_called_once_with(self.users[0], set(tags), mock.ANY)
        assert_message_in_response(res, "Question posted successfully")
        assert notifications.notify_tag_followers_new_question.call_count == len(tags)

    def test_post_question__short_title__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "short title"
        content = "question content with more than minimum chars"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(res, "Error: Title too short")
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__short_content__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "title with sufficient length"
        content = "short content"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(
            res,
            f"Error: Content should have at least {config.MIN_QUESTION_CONTENT_LENGTH} characters",
        )
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__long_content__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "title with sufficient length"
        content = "long content: " + "x" * config.MAX_QUESTION_CONTENT_LENGTH
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(res, "Error: Content too long")
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__long_title__should_fail(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "long title *" * 100
        content = "question content with more than minimum chars"
        tags = ["tag1", "tag2"]
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        self.assertEqual(0, models.Question.objects.count())
        assert_message_in_response(res, "Error: Title too long")
        self.assertContains(res, title)
        self.assertContains(res, content)

    def test_post_question__empty_tag__should_not_be_added(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = ["tag1", "  ", "tag2"]
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags))
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        assert qs.count() == 1
        q = qs[0]
        tags_list = list(t.tag_word for t in q.tags.all())
        assert len(tags_list) == 2
        for tag in ["tag1", "tag2"]:
            assert tag in tags_list, f"expected {tag} in {tags_list} but is not there"
        assert_message_in_response(res, "Question posted successfully")

    def test_post_question__with_answer__should_create_answer(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = "answer content for question with answer"
        # act
        res = self.client.add_question_post(
            title,
            content,
            ", ".join(tags),
            answereditor=answer_content,
            with_answer="on",
        )
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertTrue(q.has_accepted_answer)
        self.assertEqual(1, q.answer_set.count())
        a = q.answer_set.all()[0]
        self.assertEqual(answer_content, a.content)
        self.assertTrue(a.is_accepted)
        notifications.notify_tag_followers_new_question.assert_not_called()
        assert_message_in_response(res, "Question posted successfully")

    def test_post_question__with_answer_bad_indented_code__should_create_dedented(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = """question content with more than minimum chars
```
code indented properly code
    with several lines.
```
        """
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = """
answer content for question with answer
```
    badly indented code
        with several lines.
```
"""
        corrected_answer_content = """
answer content for question with answer
```
badly indented code
    with several lines.
```
"""
        # act
        res = self.client.add_question_post(
            title,
            content,
            ", ".join(tags),
            answereditor=answer_content,
            with_answer="on",
        )
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertTrue(q.has_accepted_answer)
        self.assertEqual(1, q.answer_set.count())
        a = q.answer_set.all()[0]
        self.assertEqual(corrected_answer_content, a.content)
        self.assertTrue(a.is_accepted)
        notifications.notify_tag_followers_new_question.assert_not_called()
        assert_message_in_response(res, "Question posted successfully")

    def test_post_question__with_answer_flag_off__should_create_answer(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = "answer content for question with answer"
        # act
        res = self.client.add_question_post(title, content, ", ".join(tags), answereditor=answer_content)
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertFalse(q.has_accepted_answer)
        self.assertEqual(0, q.answer_set.count())
        notifications.notify_tag_followers_new_question.assert_called_once_with(self.users[0], set(tags), mock.ANY)
        assert_message_in_response(res, "Question posted successfully")
        self.assertEqual(len(tags), notifications.notify_tag_followers_new_question.call_count)

    def test_post_question__with_answer_and_invites__should_ignore_invites(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = "answer content for question with answer"
        # act
        res = self.client.add_question_post(
            title,
            content,
            ", ".join(tags),
            invites=",".join(self.usernames[1:]),
            answereditor=answer_content,
            with_answer="on",
        )
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertTrue(q.has_accepted_answer)
        self.assertEqual(1, q.answer_set.count())
        a = q.answer_set.all()[0]
        self.assertEqual(answer_content, a.content)
        self.assertTrue(a.is_accepted)
        self.assertEqual(0, q.invitations.count())
        notifications.notify_tag_followers_new_question.assert_not_called()
        assert_message_in_response(res, "Question posted successfully")

    def test_post_question__with_answer_and_anonymous__should_ignore_anonymous(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        title = "question title with acceptable chars"
        content = "question content with more than minimum chars"
        tags = [
            "tag1",
        ]
        notifications.notify_tag_followers_new_question = mock.MagicMock()
        answer_content = "answer content for question with answer"
        # act
        res = self.client.add_question_post(
            title,
            content,
            ", ".join(tags),
            anonymous="on",
            answereditor=answer_content,
            with_answer="on",
        )
        # assert
        qs = models.Question.objects.filter(title=title, content=content)
        self.assertEqual(1, qs.count())
        q = qs[0]
        tags_list = list(q.tags.all())
        self.assertEqual(len(tags_list), len(tags))
        self.assertTrue(q.has_accepted_answer)
        self.assertEqual(1, q.answer_set.count())
        a = q.answer_set.all()[0]
        self.assertEqual(answer_content, a.content)
        self.assertTrue(a.is_accepted)
        self.assertFalse(q.is_anonymous)
        notifications.notify_tag_followers_new_question.assert_not_called()
        assert_message_in_response(res, "Question posted successfully")
