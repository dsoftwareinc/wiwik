from bs4 import BeautifulSoup
from django.conf import settings
from django.urls import reverse

from common.test_utils import assert_url_in_chain
from tags.tests.base import TagsApiTestCase


class TestHomeView(TagsApiTestCase):
    def test_home_template__not_logged_in__redirect(self):
        # act
        res = self.client.home()
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' + reverse('tags:list'))

    def test_home_template__green(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.home()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        tag_buttons = soup.find_all('a', {'class': 'btn-question-tag'})
        self.assertEqual(len(self.tags), len(tag_buttons))
        tag_links = {el.get('href') for el in tag_buttons}
        for tag in self.tags:
            self.assertIn(reverse('forum:tag', args=[tag.tag_word, ]), tag_links)

    def test_home_template__tag_filter_on__should_filter(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.home(tag_word='tag1')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        tag_buttons = soup.find_all('a', {'class': 'btn-question-tag'})
        self.assertEqual(1, len(tag_buttons))
        tag_links = {el.get('href') for el in tag_buttons}
        for tag in self.tags:
            self.assertIn(reverse('forum:tag', args=['tag1']), tag_links)

    def test_home_template__forum_app_not_installed__should_return_empty_watch_list(self):
        self.client.login(self.username, self.password)
        prev_INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.remove('forum')
        # act
        res = self.client.home()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        tag_buttons = soup.find_all('a', {'class': 'btn-question-tag'})
        self.assertEqual(len(self.tags), len(tag_buttons))
        tag_links = {el.get('href') for el in tag_buttons}
        for tag in self.tags:
            self.assertIn(reverse('forum:tag', args=[tag.tag_word, ]), tag_links)
        # restore
        settings.INSTALLED_APPS = prev_INSTALLED_APPS

    def test_home_template__non_existing_page__should_send_first_page(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.home(page=50)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        tag_buttons = soup.find_all('a', {'class': 'btn-question-tag'})
        self.assertEqual(len(self.tags), len(tag_buttons))
        tag_links = {el.get('href') for el in tag_buttons}
        for tag in self.tags:
            self.assertIn(reverse('forum:tag', args=[tag.tag_word, ]), tag_links)

    def test_list_query__green(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.list_query()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        tag_buttons = soup.find_all('a', {'class': 'btn-question-tag'})
        self.assertEqual(len(self.tags), len(tag_buttons))
        self.assertEqual(0, len(soup.find_all('h1', )))

        tag_links = {el.get('href') for el in tag_buttons}
        for tag in self.tags:
            self.assertIn(reverse('forum:tag', args=[tag.tag_word, ]), tag_links)
