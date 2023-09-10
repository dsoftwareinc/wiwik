import datetime

from bs4 import BeautifulSoup
from django.urls import reverse
from django.utils import timezone

from common.test_utils import assert_message_in_response, assert_url_in_chain
from forum.models import TagFollow, QuestionBookmark
from forum.views import utils
from tags.models import Tag
from userauth.jobs import log_request
from userauth.tests.utils import UserAuthTestCase


class UserAuthViewProfileTest(UserAuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        q2 = utils.create_question(cls.users[0], cls.title, cls.question_content, '')
        utils.create_question(cls.users[0], cls.title, cls.question_content, '')
        utils.create_question(cls.users[1], cls.title, cls.question_content, '')
        utils.upvote(cls.users[1], cls.question)
        utils.downvote(cls.users[1], q2)
        QuestionBookmark.objects.create(user=cls.users[1], question=cls.question)
        log_request(cls.users[0].id, '127.0.0.1',
                    timezone.now() - datetime.timedelta(days=500), 200,
                    'GET', '/path')
        log_request(cls.users[1].id, '174.95.73.69', timezone.now(),
                    200, 'GET', '/path')

    def test_view_profile__own_profile__green(self):
        # arrange
        self.client.login(self.usernames[1], self.password)

        # multi tabs test
        for tab in self.tabs:
            res = self.client.view_profile(self.usernames[1], tab)
            # assert
            assert res.status_code == 200
            assert reverse('userauth:edit') in str(res.content)  # show edit button
            soup = BeautifulSoup(res.content, 'html.parser')
            tab_headers = soup.find_all('a', {'class': 'profile-tab-link'})
            self.assertEqual(len(self.tabs), len(tab_headers))
            self.assertEqual(1, len(soup.find_all('a', {
                'class': 'profile-tab-link',
                'aria-selected': 'true',
            })))
            self.assertEqual(1, len(soup.find_all('a', {
                'class': 'profile-tab-link',
                'aria-controls': tab,
                'aria-selected': 'true',
            })))

    def test_view_profile__different_user__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_profile(self.usernames[1], 'questions')
        # assert
        self.assertContains(res, 'Last visited', status_code=200)
        self.assertNotContains(res, 'logos/Keybase_logo_official.png')
        assert res.status_code == 200
        assert reverse('userauth:edit') not in str(res.content)  # don't show edit button

    def test_view_profile__user_not_following_questions__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_profile(self.usernames[2], 'following')
        # assert
        self.assertContains(res, 'No questions followed', status_code=200)

    def test_view_profile__following_tab_tags_with_description__show_popover(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        tag = Tag.objects.all().first()
        tag.description = 'TAG_DESCRIPTION'
        tag.experts = self.users[0].username
        tag.stars = self.users[0].username
        tag.save()
        TagFollow.objects.filter(user=self.users[0]).update(reputation=10)
        # act
        res = self.client.view_profile(self.usernames[0], 'following')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(2, len(soup.find_all('a', {'class': 'btn btn-question-tag m-2'})))

    def test_view_profile__different_user_with_github__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        self.users[1].github_handle = 'cunla'
        self.users[1].keybase_user = 'danielm'
        self.users[1].save()
        # act
        res = self.client.view_profile(self.usernames[1], 'questions')
        # assert
        self.assertContains(res, 'Last visited', status_code=200)
        self.assertContains(res, 'Canada')
        self.assertContains(res, 'logo-github')
        self.assertContains(res, 'logos/Keybase_logo_official.png')
        assert res.status_code == 200
        assert reverse('userauth:edit') not in str(res.content)  # don't show edit button

    def test_view_profile__different_user_inactive__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        self.users[1].is_active = False
        self.users[1].save()
        # act
        res = self.client.view_profile(self.usernames[1], 'questions')
        # assert
        self.assertContains(res, 'Member inactive', status_code=200)

    def test_view_profile__different_user__reputation_should_not_be_unseen(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        res = self.client.view_profile(self.usernames[0], 'reputation')
        self.assertContains(res, 'bg-unseen')
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.view_profile(self.usernames[0], 'reputation')
        # assert
        self.assertEqual(200, res.status_code)
        assert reverse('userauth:edit') not in str(res.content)  # don't show edit button
        self.assertNotContains(res, 'bg-unseen')

    def test_view_profile__non_existing_user(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        username = 'user_not_there'
        # act
        res = self.client.view_profile(username, 'questions')
        # assert
        assert res.status_code == 200
        assert_url_in_chain(res, reverse('forum:list'))
        assert_message_in_response(res, f"Couldn't find user {username}")

    def test_view_profile__non_existing_page__returns_first_page(self):
        # arrange
        self.client.login(self.usernames[1], self.password)

        # act
        res = self.client.view_profile(self.usernames[1], 'questions', 20)
        # assert
        assert res.status_code == 200

    def test_view_profile__non_existing_tab__returns_questions_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)

        # act
        res = self.client.view_profile(self.usernames[0], 'non_existing_tab')
        # assert
        assert res.status_code == 200
        soup = BeautifulSoup(res.content, 'html.parser')
        tab_headers = soup.find_all('a', {'class': 'profile-tab-link'})
        self.assertEqual(len(self.tabs), len(tab_headers))
        self.assertEqual(1, len(soup.find_all('a', {
            'class': 'profile-tab-link',
            'aria-selected': 'true',
        })))
        self.assertEqual(1, len(soup.find_all('a', {
            'class': 'profile-tab-link',
            'aria-controls': 'questions',
            'aria-selected': 'true',
        })))


class TestProfilePagination(UserAuthTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for i in range(50):
            utils.create_question(
                cls.users[1], cls.title, cls.question_content, cls.tags[0])

    def test_view_profile__pagination_middle_page__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_profile(self.usernames[1], 'questions', page=2)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        pagination_tags = soup.find_all('nav', {'aria-label': 'Page navigation'})
        self.assertEqual(1, len(pagination_tags))
        self.assertEqual(2, len(soup.find_all('a', {'href': '?page=1'})))
        self.assertEqual(2, len(soup.find_all('a', {'href': '?page=3'})))

    def test_view_profile__pagination_first_page__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_profile(self.usernames[1], 'questions', page=1)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        pagination_tags = soup.find_all('nav', {'aria-label': 'Page navigation'})
        self.assertEqual(1, len(pagination_tags))
        self.assertEqual(2, len(soup.find_all('a', {'href': '?page=2'})))
        self.assertEqual(1, len(soup.find_all('a', {'href': '?page=3'})))

    def test_view_profile__pagination_last_page__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.view_profile(self.usernames[1], 'questions', page=3)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        pagination_tags = soup.find_all('nav', {'aria-label': 'Page navigation'})
        self.assertEqual(1, len(pagination_tags))
        self.assertEqual(2, len(soup.find_all('a', {'href': '?page=2'})))

    def test_header__user_with_badges__show_badge(self):
        self.client.login(self.usernames[0], self.password)
        self.users[0].gold_badges = 2
        self.users[0].silver_badges = 2
        self.users[0].bronze_badges = 2
        self.users[0].save()
        # act
        res = self.client.view_profile(self.usernames[1], 'questions')
        navbar_res = self.client.view_user_navbar()
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(200, navbar_res.status_code)
        soup = BeautifulSoup(navbar_res.content, 'html.parser')
        self.assertEqual(1, len(soup.find_all('span', {'class': 'mx-1 text-gold'})))
        self.assertEqual(1, len(soup.find_all('span', {'class': 'mx-1 text-silver'})))
        self.assertEqual(1, len(soup.find_all('span', {'class': 'mx-1 text-bronze'})))
