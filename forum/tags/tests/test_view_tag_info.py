from django.urls import reverse

from common.test_utils import assert_url_in_chain
from tags.tests.base import TagsApiTestCase


class TestInfoTag(TagsApiTestCase):
    def test_info_tag_get__not_logged_in__redirect(self):
        tag_word = "tag1"
        # act
        res = self.client.info(tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse(
                "tags:info",
                args=[
                    tag_word,
                ],
            ),
        )

    def test_info_tag_get__green(self):
        tag_word = "tag1"
        self.client.login(self.username, self.password)
        # act
        res = self.client.info(tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, "Usage guidance (excerpt)")
