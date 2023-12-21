from django.urls import reverse

from common.test_utils import assert_url_in_chain
from forum import models
from forum.tests.base import ForumApiTestCase
from wiwik_lib.views.follow_views import create_follow


class TestFollowTagView(ForumApiTestCase):
    tag_word = "my_first_tag"

    def setUp(self):
        super().setUp()
        self.tag = models.Tag.objects.create(tag_word=self.tag_word)

    def test_follow_tag__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.follow_tag(self.tag_word)
        # assert
        self.assertEqual(
            0,
            models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count(),
        )
        self.assertEqual(1, self.tag.follows.count())
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word,
                ],
            ),
        )
        self.assertContains(res, "Watched tags")

    def test_follow_tag__non_existing_tag__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.follow_tag(self.tag_word + "aa")
        # assert
        models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count()
        self.assertEqual(
            0,
            models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count(),
        )
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word + "aa",
                ],
            ),
        )
        self.assertNotContains(res, "Watched tags")

    def test_follow_tag__already_following__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        create_follow(self.tag, self.users[0])
        # act
        res = self.client.follow_tag(self.tag_word)
        # assert
        self.assertEqual(1, self.tag.follows.count())
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word,
                ],
            ),
        )
        self.assertContains(res, "Watched tags")


class TestUnfollowTagView(ForumApiTestCase):
    tag_word = "my_first_tag"

    def setUp(self):
        super().setUp()
        self.tag = models.Tag.objects.create(tag_word=self.tag_word)

    def test_unfollow_tag__green(self):
        self.client.login(self.usernames[0], self.password)
        models.UserTagStats.objects.create(user=self.users[0], tag=self.tag)
        # act
        res = self.client.unfollow_tag(self.tag_word)
        # assert
        self.assertEqual(
            0,
            models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count(),
        )
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word,
                ],
            ),
        )
        self.assertNotContains(res, "Watched tags")

    def test_unfollow_tag__user_not_following__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.unfollow_tag(self.tag_word)
        # assert
        self.assertEqual(
            0,
            models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count(),
        )
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word,
                ],
            ),
        )
        self.assertNotContains(res, "Watched tags")

    def test_unfollow_tag__non_existing_tag__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.unfollow_tag(self.tag_word + "aaa")
        # assert
        self.assertEqual(
            0,
            models.UserTagStats.objects.filter(user=self.users[0], tag=self.tag).count(),
        )
        assert_url_in_chain(
            res,
            reverse(
                "forum:tag",
                args=[
                    self.tag_word + "aaa",
                ],
            ),
        )
        self.assertNotContains(res, "Watched tags")
