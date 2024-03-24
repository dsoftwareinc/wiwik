from constance import config
from django.urls import reverse

from common.test_utils import assert_message_in_response, assert_url_in_chain
from tags.models import Tag
from tags.tests.base import TagsApiTestCase


class TestEditTag(TagsApiTestCase):
    new_description = "New description for tag with 20 chars" + "X" * max(config.MIN_TAG_DESCRIPTION_LENGTH - 37, 0)
    new_wiki = "New wiki for tag with more than 20 chars"
    summary = "Edit summary" + "X" * max(config.MIN_TAG_EDIT_SUMMARY_LENGTH - 12, 0)

    def test_edit_tag_get__not_logged_in__redirect(self):
        # act
        res = self.client.edit_get(self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse(
                "tags:edit",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )

    def test_edit_tag_post__not_logged_in__redirect(self):
        # act
        res = self.client.edit_post(self.tags[0].tag_word, self.new_description, self.new_wiki, self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse(
                "tags:edit",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )

    def test_edit_tag_get__green(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_get(self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, "Usage guidance (excerpt)")

    def test_edit_tag_post__green(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, self.new_description, self.new_wiki, self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, f"Tag {self.tags[0].tag_word} edited successfully")
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertEqual(self.new_description, tag.description)
        self.assertEqual(self.new_wiki, tag.wiki)
        self.assertEqual(1, tag.tagedit_set.count())
        self.assertEqual(self.summary, tag.tagedit_set.first().summary)

    def test_edit_tag_post__change_only_description(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, self.new_description, self.tags[0].wiki, self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, f"Tag {self.tags[0].tag_word} edited successfully")
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(1, tag.tagedit_set.count())
        self.assertEqual(self.summary, tag.tagedit_set.first().summary)

    def test_edit_tag_post__twice_by_same_user__should_have_one_edit(self):
        self.client.login(self.username, self.password)
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        self.client.edit_post(self.tags[0].tag_word, self.new_description, self.new_wiki, self.summary)
        # act
        res = self.client.edit_post(
            self.tags[0].tag_word,
            self.new_description,
            self.new_wiki + "2",
            self.summary,
        )
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, f"Tag {self.tags[0].tag_word} edited successfully")
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertEqual(self.new_description, tag.description)
        self.assertEqual(self.new_wiki + "2", tag.wiki)
        self.assertEqual(1, tag.tagedit_set.count())
        self.assertEqual(self.summary, tag.tagedit_set.first().summary)

    def test_edit_tag_post__description_too_short__should_fail(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, "very short", self.new_wiki, self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, "Error: Description too short")
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__no_changes__should_fail(self):
        self.client.login(self.username, self.password)
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, tag.description, tag.wiki, self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, f"No changes made in tag {self.tags[0].tag_word} data")
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__wiki_too_short__should_fail(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, self.new_description, "very short", self.summary)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(
            res,
            "Error: Wiki content should have " f"at least {config.MIN_TAG_WIKI_LENGTH} characters",
        )
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__description_too_long__should_fail(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(
            self.tags[0].tag_word,
            self.new_description + "x" * config.MAX_TAG_DESCRIPTION_LENGTH,
            self.new_wiki,
            self.summary,
        )
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(
            res,
            f"Error: Description too long, max is {config.MAX_TAG_DESCRIPTION_LENGTH} characters",
        )
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__wiki_too_long__should_fail(self):
        tag_word = self.tags[0].tag_word
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(
            tag_word,
            self.new_description,
            "very long" + "x" * config.MAX_TAG_WIKI_LENGTH,
            self.summary,
        )
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(res, "Error: Wiki content too long")
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__summary_too_short__should_fail(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(self.tags[0].tag_word, self.new_description, self.new_wiki, "X")
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(
            res,
            "Error: Edit summary should have " f"at least {config.MIN_TAG_EDIT_SUMMARY_LENGTH} characters",
        )
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())

    def test_edit_tag_post__summary_too_long__should_fail(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.edit_post(
            self.tags[0].tag_word,
            self.new_description,
            self.new_wiki,
            "long" + "X" * config.MAX_TAG_EDIT_SUMMARY_LENGTH,
        )
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse(
                "tags:info",
                args=[
                    self.tags[0].tag_word,
                ],
            ),
        )
        assert_message_in_response(
            res,
            "Error: Edit summary too long, " f"max is {config.MIN_TAG_EDIT_SUMMARY_LENGTH} characters",
        )
        tag = Tag.objects.get(tag_word=self.tags[0].tag_word)
        tag.refresh_from_db()
        self.assertNotEqual(self.new_description, tag.description)
        self.assertNotEqual(self.new_wiki, tag.wiki)
        self.assertEqual(0, tag.tagedit_set.count())
