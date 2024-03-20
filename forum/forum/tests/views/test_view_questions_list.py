from unittest import mock

from bs4 import BeautifulSoup
from constance import config
from django.conf import settings
from django.test import override_settings
from django.urls import reverse

from common.test_utils import assert_url_in_chain, assert_message_in_response
from common.utils import TabEnum
from forum import models
from forum.jobs.others import log_search
from forum.tests.base import ForumApiTestCase
from forum.views import utils, follow_models
from userauth.models import ForumUser


class TestForumQuestionsListView(ForumApiTestCase):
    tags = ["my_first_tag", "my_second_tag"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        num_users = len(cls.users)
        for i in range(config.QUESTIONS_PER_PAGE + 2):
            utils.create_question(
                cls.users[i % num_users],
                cls.title,
                cls.question_content,
                ",".join(cls.tags),
            )

    def test_questions_list__empty_list_user_not_loggedin_default_tab(self):
        # act
        res = self.client.questions_list()
        # assert
        self.assertContains(res, "Login")
        assert_url_in_chain(res, reverse("userauth:login") + "?next=" + reverse("forum:list"))

    def test_questions_list__empty_list_user_loggedin_default_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.questions_list()
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertNotContains(res, "Login")

    def test_questions_list__user_loggedin_default_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.questions_list()
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__anonymous_question__should_not_show_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = self.users[0]
        utils.create_question(
            user,
            self.title,
            self.question_content,
            ",".join(self.tags),
            is_anonymous=True,
        )
        # act
        res = self.client.questions_list()
        # assert
        self.assertContains(res, "Asked anonymously")

    def test_questions_list__latest_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = self.users[0]
        utils.create_question(user, self.title, self.question_content, ",".join(self.tags))
        # act
        res = self.client.questions_list(tab=TabEnum.LATEST.value)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)
        soup = BeautifulSoup(res.content, "html.parser")
        assert "active" in soup.find(text="Latest").parent.parent.get("class")
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__mostviewed_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = self.users[0]
        utils.create_question(user, self.title, self.question_content, ",".join(self.tags))
        # act
        res = self.client.questions_list(tab=TabEnum.MOST_VIEWED.value)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)

        soup = BeautifulSoup(res.content, "html.parser")
        assert "active" in soup.find(text="Most viewed").parent.parent.get("class")
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__unresolved_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = self.users[0]
        utils.create_question(user, self.title, self.question_content, ",".join(self.tags))
        # act
        res = self.client.questions_list(tab=TabEnum.UNRESOLVED.value)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)

        soup = BeautifulSoup(res.content, "html.parser")
        assert "active" in soup.find(text="Not resolved").parent.parent.get("class")
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__unanswered_tab(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = self.users[0]
        utils.create_question(user, self.title, self.question_content, ",".join(self.tags))
        # act
        res = self.client.questions_list(tab=TabEnum.UNANSWERED.value)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)
        soup = BeautifulSoup(res.content, "html.parser")
        assert "active" in soup.find(text="Unanswered").parent.parent.get("class")
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__non_existing_page(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.questions_list(page=20)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(
            res,
            '<span class="page-link">2 <span class="sr-only">(current)</span></span>',
        )
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    def test_questions_list__existing_page(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.questions_list(page=2)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "All questions")
        self.assertContains(res, "Ask Question")
        self.assertContains(
            res,
            '<span class="page-link">2 <span class="sr-only">(current)</span></span>',
        )
        self.assertContains(res, self.title)
        for tag_word in self.tags:
            self.assertContains(res, tag_word)
        self.assertNotContains(res, self.question_content)

    @override_settings(
        MEILISEARCH_ENABLED=False,
        RUN_ASYNC_JOBS_SYNC=True,
    )
    @mock.patch("forum.jobs.start_job")
    def test_questions_list__query_title(self, start_job: mock.MagicMock):
        # arrange
        title_to_file = "unique title"
        self.client.login(self.usernames[1], self.password)
        # prev_search_count = self.users[0].search_count
        utils.create_question(self.users[0], title_to_file, self.question_content, ",".join(self.tags))
        # act
        res = self.client.questions_list(query=title_to_file)
        # assert
        self.assertContains(res, self.usernames[0])
        self.assertContains(res, "Search results")
        self.assertContains(res, "Ask Question")
        self.assertContains(res, title_to_file)
        self.assertNotContains(res, self.question_content)
        start_job.assert_has_calls(
            [
                mock.call(log_search, self.users[1], title_to_file, mock.ANY, mock.ANY),
            ],
            any_order=True,
        )


class TestForumQuestionsForTag(ForumApiTestCase):
    username = "myusername"
    tag_word = "my_first_tag"
    tag_description = "my tag description with many things"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tag = models.Tag.objects.create(tag_word=cls.tag_word, description=cls.tag_description)
        cls.tag.experts = cls.username
        cls.tag.stars = cls.username
        cls.tag.save()

    def test_questions_tag__user_loggedin(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        user = ForumUser.objects.get(username=self.usernames[1])
        utils.create_question(user, self.title, self.question_content, self.tag_word)
        # act
        res = self.client.questions_list_for_tag(self.tag_word)
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)
        self.assertContains(res, self.tag_word)
        self.assertContains(res, self.tag_description)
        self.assertNotContains(res, "<h2><b>All questions")
        self.assertNotContains(res, self.question_content)

    def test_questions_tag__bad_tag_name(self):
        # arrange
        bad_tag_word = "not_existing_tag"
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.questions_list_for_tag(bad_tag_word)
        # assert
        assert_message_in_response(res, f"Tag {bad_tag_word} does not exist")
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse("forum:list"))


class TestHomeView(ForumApiTestCase):
    def test_home__user_loggedin(self):
        # arrange
        tag_word = "my_first_tag"
        tag_description = "my tag description with many things"
        self.client.login(self.usernames[1], self.password)
        user = self.users[1]
        tag = models.Tag.objects.create(tag_word="my_first_tag", description=tag_description)
        follow_models.create_follow_tag(tag, user)
        utils.create_question(user, self.title, self.question_content, tag_word)
        # act
        res = self.client.home()
        # assert
        self.assertContains(res, self.usernames[1])
        self.assertContains(res, "Ask Question")
        self.assertContains(res, self.title)
        self.assertContains(res, tag_word)
        self.assertContains(res, tag_description)
        self.assertContains(res, "Home")
        self.assertNotContains(res, self.question_content)

    def test_home__no_user_tag_stats_for_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.home()
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse("forum:list"))
        assert_message_in_response(
            res,
            "You need to follow tags so your home page will be adjusted for you, "
            "meanwhile you can see all the questions in the forum",
        )

    def test_home__should_not_duplicate_questions(self):
        # arrange
        tag_description = "my tag description with many things"
        self.client.login(self.usernames[1], self.password)
        user = self.users[1]
        for i in range(3):
            tag = models.Tag.objects.create(tag_word=f"tag{i}", description=tag_description)
            follow_models.create_follow_tag(tag, user)
        tag_str = ",".join([f"tag{i}" for i in range(3)])
        utils.create_question(user, self.title, self.question_content, tag_str)
        # act
        res = self.client.home()
        # assert
        soup = BeautifulSoup(res.content, "html.parser")
        self.assertEqual(1, len(soup.find_all("div", {"class": "summary"})))
        watched_tags_div = soup.find("div", {"id": "watched-tags"})
        self.assertIsNotNone(watched_tags_div)
        self.assertEqual(3, len(watched_tags_div.find_all("a")))

    def test_questions_list__tags_with_experts_and_stars__should_show_in_popover(self):
        # arrange
        tag_description = "my tag description with many things"
        self.client.login(self.usernames[1], self.password)
        user = self.users[1]
        tags_list = list()
        for i in range(3):
            tag = models.Tag.objects.create(tag_word=f"tag{i}", description=tag_description if i > 0 else None)
            follow_models.create_follow_tag(tag, user)
            tags_list.append(tag)
        tag_str = ",".join([f"tag{i}" for i in range(3)])
        utils.create_question(user, self.title, self.question_content, tag_str)
        for tag in tags_list:
            tag.experts = self.usernames[2]
            tag.stars = self.usernames[2]
            tag.save()
        # act
        res = self.client.questions_list()
        # assert
        self.assertContains(res, "Leaders:")
        self.assertContains(res, "Rising stars:")
        self.assertContains(res, self.usernames[2])
