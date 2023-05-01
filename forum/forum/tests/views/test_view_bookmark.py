from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestBookmarkQuestionView(ForumApiTestCase):
    title = 'my_question_title'
    question_content = 'my_question_content_with more than 20 chars'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.question = utils.create_question(cls.users[1], cls.title, cls.question_content, ','.join(cls.tags))

    def test_bookmark_question__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.bookmark_question(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, models.QuestionBookmark.objects.all().count())
        self.assertEqual(1, self.users[0].bookmarks_count)

    def test_bookmark_question__existing_bookmark__should_not_create(self):
        self.client.login(self.usernames[0], self.password)
        models.QuestionBookmark.objects.create(user=self.users[0], question=self.question)
        # act
        res = self.client.bookmark_question(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, models.QuestionBookmark.objects.all().count())
        self.assertEqual(1, self.users[0].bookmarks_count)

    def test_bookmark_question__non_existing_question__should_not_create(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.bookmark_question(self.question.pk + 20)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionBookmark.objects.all().count())
        self.users[0].refresh_from_db()
        self.assertEqual(0, self.users[0].bookmarks_count)

    def test_unbookmark_question__green(self):
        self.client.login(self.usernames[0], self.password)
        models.QuestionBookmark.objects.create(user=self.users[0], question=self.question)
        # act
        res = self.client.unbookmark_question(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionBookmark.objects.all().count())
        self.users[0].refresh_from_db()
        self.assertEqual(0, self.users[0].bookmarks_count)

    def test_unbookmark_question__non_existing_bookmark__should_not_do_anything(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.unbookmark_question(self.question.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionBookmark.objects.all().count())
        self.users[0].refresh_from_db()
        self.assertEqual(0, self.users[0].bookmarks_count)

    def test_unbookmark_question__non_existing_question__should_not_create(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.unbookmark_question(self.question.pk + 20)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, models.QuestionBookmark.objects.all().count())
        self.users[0].refresh_from_db()
        self.assertEqual(0, self.users[0].bookmarks_count)
