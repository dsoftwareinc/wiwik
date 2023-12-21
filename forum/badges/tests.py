import re

from bs4 import BeautifulSoup
from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from badges import logic
from badges.models import Badge
from badges.populate_db import upsert_badges_in_db
from common.test_utils import assert_url_in_chain
from forum.models import VoteActivity
from userauth.models import ForumUser

MATCH_ALL = r".*"


def like(string):
    """
    Return a compiled regular expression that matches the given
    string with any prefix and postfix, e.g. if string = "hello",
    the returned regex matches r".*hello.*"
    """
    string_ = string
    if not isinstance(string_, str):
        string_ = str(string_)
    regex = MATCH_ALL + re.escape(string_) + MATCH_ALL
    return re.compile(regex, flags=re.DOTALL)


class BadgesClient(Client):
    def login(self, username: str, password: str):
        return super().login(username=username, password=password)

    def badges_list(self):
        return self.get(reverse("badges:list"), follow=True)

    def single_badge_users_list(self, badge_id: int):
        url = reverse(
            "badges:detail",
            args=[
                badge_id,
            ],
        )
        return self.get(url, follow=True)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f"admin:badges_{model}_changelist")
        if query is not None:
            url += f"?{query}"
        return self.get(url, follow=True)

    def admin_change(self, model: str, pk: int):
        url = reverse(
            f"admin:badges_{model}_change",
            args=[
                pk,
            ],
        )
        return self.get(url, follow=True)


@override_settings(SKIP_USER_VISIT_LOG=True)
class BadgesApiTestCase(TestCase):
    password = "1111"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        upsert_badges_in_db()
        badge_qs = Badge.objects.all()
        cls.badge = badge_qs[0]
        cls.users = list()
        for badge in badge_qs:
            u = ForumUser.objects.create_user(f"user_{badge.name}", f"user_{badge.name}@a.com", cls.password)
            VoteActivity.objects.create(badge=badge, target=u)
            cls.users.append(u)

    def setUp(self):
        self.client = BadgesClient()


class TestBadgesListView(BadgesApiTestCase):
    def test_badges_list_view__user_not_logged_in__should_redirect(self):
        res = self.client.badges_list()
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse("userauth:login") + "?next=" + reverse("badges:list"))

    def test_badges_list_view__green(self):
        # arrange
        self.client.login(self.users[0].username, self.password)
        # act
        res = self.client.badges_list()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, "html.parser")
        # Number of h3 should be len(logic.badges) + 1 for 'Recent badges' section on the side
        self.assertEqual(1 + len(logic.badges), len(soup.find_all("h3")))
        badge_qs = Badge.objects.all()
        for badge in badge_qs:
            badge_row_list = soup.find_all("div", {"id": f"badge_{badge.name}"})
            self.assertEqual(1, len(badge_row_list))
            badge_row = badge_row_list[0]
            self.assertEqual(1, len(badge_row.find_all(text=like("1 awarded"))))


class TestSingleBadgeUsersListView(BadgesApiTestCase):
    def test_view_single_badge__user_not_logged_in__should_redirect(self):
        res = self.client.single_badge_users_list(self.badge.id)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse(
                "badges:detail",
                args=[
                    self.badge.id,
                ],
            ),
        )

    def test_view_single_badge__green(self):
        # arrange
        self.client.login(self.users[0].username, self.password)
        res = self.client.single_badge_users_list(self.badge.id)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, "html.parser")
        users_list = soup.find_all("div", {"class": "user-card-container"})
        self.assertEqual(1, len(users_list))


class BadgesAdminTest(BadgesApiTestCase):
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )

    def test_admin_badges_changelist__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("badge")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_badges_change__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_change("badge", Badge.objects.all()[0].id)
        # assert
        self.assertEqual(200, res.status_code)
