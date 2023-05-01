from bs4 import BeautifulSoup
from django.test.utils import override_settings

import forum.views.search
from forum.models import Question
from forum.tests.base import ForumApiTestCase
from forum.views import utils


@override_settings(MEILISEARCH_ENABLED=False)
class TestSearch(ForumApiTestCase):
    question_title = 'my question title'
    question_content = 'My question content'
    answer_content = 'My answer content'
    tags = ['my_first_tag', 'my_second_tag', 'my_third_tag']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        forum.views.search.query_method = forum.views.search.sqlite3_query_method
        cls.questions = [
            utils.create_question(user, cls.question_title, cls.question_content, ','.join(cls.tags))
            for user in cls.users
        ]
        cls.questions.extend([
            utils.create_question(user, cls.question_title, cls.question_content, cls.tags[0])
            for user in cls.users
        ])
        utils.create_answer(cls.answer_content, cls.users[0], cls.questions[0])
        utils.upvote(cls.users[0], cls.questions[1])
        utils.upvote(cls.users[0], cls.questions[2])
        utils.upvote(cls.users[1], cls.questions[0])
        utils.upvote(cls.users[1], cls.questions[2])
        a = utils.create_answer(cls.answer_content, cls.users[0], cls.questions[1])
        a.is_accepted = True
        a.save()

    def test_search_basic__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='my question title')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.users) * 2, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__bad_quotes__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='my question "title')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.users) * 2, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__bad_quotes_2nd__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='TesT(\')(,",))')
        # assert
        self.assertEqual(200, res.status_code)

    def test_search__bad_quotes_3rd__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='\'')
        # assert
        self.assertEqual(200, res.status_code)

    def test_search__username__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query=f'user:{self.usernames[0]} "my question title"')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(2, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__tag__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query=f'[{self.tags[2]}]')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        num_results = Question.objects.filter(tags__tag_word__iexact=self.tags[2]).count()
        self.assertEqual(num_results, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__multiple_tags__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query=f'[{self.tags[2]}] [{self.tags[0]}]')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        num_results = (Question.objects
                       .filter(tags__tag_word__iexact=self.tags[2])
                       .filter(tags__tag_word__iexact=self.tags[0])
                       .count())
        self.assertEqual(num_results, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__one_answer__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='answers:1')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(2, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__no_answers__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='answers:0')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.questions) - 2, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__resolved__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='resolved:yes')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__score_is_2__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='score:2')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__score_is_1__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='score:1')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'summary'})))

    def test_search__score_is_nan__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.questions_list(query='score:dsa')
        # assert
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.questions), len(soup.find_all('div', {'class': 'summary'})))
