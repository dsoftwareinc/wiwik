from bs4 import BeautifulSoup
from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum.models import VoteActivity
from forum.views import utils
from userauth.tests.utils import UserAuthTestCase


class UsersViewTest(UserAuthTestCase):
    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    tags = ['my_first_tag', ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))
        VoteActivity.objects.create(source=None,
                                    target=cls.users[1],
                                    reputation_change=10,
                                    question=question)

    def test__users_list__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test__users_list__not_logged_in(self):
        # act
        res = self.client.users()
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('userauth:login') + '?next=' + reverse(
            'userauth:list') + "%3Ftab%3Dall%26")

    def test_users_list__query_user(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users(user=self.usernames[0][:len(self.usernames[0]) - 1])
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(2, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test_users_list__monthly_tab(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users(tab='month')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test_users_list__all_tab(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users(tab='all')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test_users_list__with_one_moderator__should_show_moderator_badge(self):
        self.client.login(self.usernames[0], self.password)
        self.users[1].is_moderator = True
        self.users[1].save()
        # act
        res = self.client.users(tab='all')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'user-list-card'})))
        self.assertEqual(1, len(soup.find_all('span', {'class': 'btn btn-moderator-tag'})))

    def test_users_list__with_from_date__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users(from_date='2021-01-01')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test_users_list__non_existing_page__show_page_one(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users(page=50, )
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'user-list-card'})))

    def test__users_query__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.users_list_query()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(3, len(soup.find_all('div', {'class': 'user-list-card'})))
        self.assertEqual(0, len(soup.find_all('div', {'class': 'pagination pagination-md pull-right p-2'})))
