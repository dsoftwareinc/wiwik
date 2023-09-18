from unittest import mock

from django.urls import reverse

from forum.tests.base import ForumApiTestCase
from forum.views import utils


class TestSlack(ForumApiTestCase):
    question_title = 'How much does wiwik cost?'
    question_content = 'What subscription fee are you charging?'
    tags = ['my_first_tag', ]

    @mock.patch('forum.views.integrations.slack_views.slack_api.verify_request')
    @mock.patch('forum.views.integrations.slack_views.search.query_method')
    def test_search_from_slack(self, mock_query, mock_verify_request):
        q = utils.create_question(self.users[0], self.question_title, self.question_content, ','.join(self.tags))
        mock_verify_request.return_value = True
        query_result = mock.MagicMock()
        query_result.order_by.return_value = [q, ]
        mock_query.return_value = query_result
        res = self.client.post(
            reverse('forum:slack-search'),
            data={'text': 'subscription'}
        )

        # assert
        self.assertEqual(200, res.status_code)
        response = res.json()
        self.assertEqual(self.question_title, response['blocks'][0]['text']['text'])
        self.assertEqual(self.question_content, response['blocks'][1]['text']['text'])
