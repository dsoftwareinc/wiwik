import json

from django.urls import reverse

from common.test_utils import assert_url_in_chain
from tags.models import Tag
from tags.tests.base import TagsApiTestCase


class TestAutocompleteView(TagsApiTestCase):
    def test_autocomplete__not_logged_in__redirect(self):
        # act
        res = self.client.autocomplete(None)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res,
                            reverse('userauth:login') + '?next=' + reverse('tags:autocomplete'))

    def test_autocomplete__no_query__green(self):
        self.client.login(self.username, self.password)
        # act
        res = self.client.autocomplete(None)
        # assert
        self.assertEqual(200, res.status_code)
        res_dict = json.loads(res.content)
        self.assertIn('results', res_dict)
        results = res_dict['results']
        self.assertEqual(len(self.tags), len(results))

    def test_autocomplete__query__green(self):
        self.client.login(self.username, self.password)
        tag_word = 'tag1'
        # act
        res = self.client.autocomplete(tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        res_dict = json.loads(res.content)
        self.assertIn('results', res_dict)
        results = res_dict['results']
        tags_fit_count = Tag.objects.filter(tag_word__icontains=tag_word).count()
        self.assertEqual(tags_fit_count, len(results))
