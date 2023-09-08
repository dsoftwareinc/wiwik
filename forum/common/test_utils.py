from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse


def assert_url_in_chain(response, url):
    chain = [i[0] for i in response.redirect_chain]
    assert url in chain, f'expected {url} in {chain}'


def assert_message_in_response(response, message):
    messages = [m.message for m in get_messages(response.wsgi_request)]
    assert message in messages, f'expected "{message}" in {messages}'


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_called_with(*args, **kwargs)
    except AssertionError:
        return
    raise AssertionError('Expected %s to not have been called.' % self._format_mock_call_signature(args, kwargs))


class ForumClient:
    def __init__(self):
        self.client = Client()

    def login(self, username: str, password: str):
        return self.client.login(username=username, password=password)

    def questions_list(self, page=None, tab=None, query=None):
        url = reverse('forum:list') + '?'
        if page is not None:
            url += f'page={page}&'
        if tab is not None:
            url += f'tab={tab}&'
        if query is not None:
            url += f'q={query}&'
        return self.client.get(url, follow=True)

    def home(self, page=None, tab=None, query=None):
        url = reverse('forum:home') + '?'
        if page is not None:
            url += f'page={page}&'
        if tab is not None:
            url += f'tab={tab}&'
        if query is not None:
            url += f'q={query}&'
        return self.client.get(url, follow=True)

    def questions_list_for_tag(self, tag: str, tab=None, query=None):
        url = reverse('forum:tag', args=[tag]) + '?'
        if tab is not None:
            url += f'tab={tab}&'
        if query is not None:
            url += f'q={query}&'
        return self.client.get(url, follow=True)

    def add_question_post(self, title: str, content: str, tags: str, **kwargs):
        url = reverse('forum:ask')
        data = {'title': title,
                'queseditor': content,
                'tags': tags,
                }
        for extra in ['anonymous', 'invites', 'with_answer', 'answereditor']:
            if extra in kwargs:
                data[extra] = kwargs[extra]
        return self.client.post(url, data, follow=True)

    def add_question_get(self):
        url = reverse('forum:ask')
        return self.client.get(url, follow=True)

    def edit_question_get(self, question_pk: int):
        url = reverse('forum:question_edit', args=[question_pk, ])
        return self.client.get(url, follow=True)

    def edit_question_post(self, question_pk: int, title: str, content: str, tags: str):
        url = reverse('forum:question_edit', args=[question_pk, ])
        return self.client.post(url,
                                {'title': title,
                                 'queseditor': content,
                                 'tags': tags,
                                 },
                                follow=True)

    def edit_answer_get(self, answer_pk: int):
        url = reverse('forum:answer_edit', args=[answer_pk, ])
        return self.client.get(url, follow=True)

    def edit_answer_post(self, answer_pk: int, content: str):
        url = reverse('forum:answer_edit', args=[answer_pk, ])
        return self.client.post(
            url, {
                'queseditor': content,
            },
            follow=True)

    def view_thread_get(self, question_pk: int, order_by: str = None):
        url = reverse('forum:thread', args=[question_pk, ]) + '?'
        if order_by is not None:
            url += f'order_by={order_by}&'
        return self.client.get(url, follow=True)

    def thread_add_comment(self, question_pk, model, model_pk, comment_content):
        return self.client.post(reverse('forum:thread', args=[question_pk, ]),
                                {'action': 'create_comment',
                                 'model': model,
                                 'model_pk': model_pk,
                                 'comment': comment_content,
                                 },
                                follow=True)

    def thread_add_answer(self, question_pk, answer_content):
        return self.client.post(reverse('forum:thread', args=[question_pk, ]),
                                {'action': 'create_answer', 'editor1': answer_content, },
                                follow=True)

    def thread_unknown_post_action(self, question_pk, **kwargs):
        return self.client.post(reverse('forum:thread', args=[question_pk, ]),
                                {'action': 'unknown_post_action', **kwargs},
                                follow=True)

    def upvote(self, question_pk, model, model_pk):
        return self.client.get(
            reverse('forum:upvote', args=[question_pk, model, model_pk]),
            follow=True)

    def downvote(self, question_pk, model, model_pk):
        return self.client.get(
            reverse('forum:downvote', args=[question_pk, model, model_pk]),
            follow=True)

    def accept_answer(self, question_pk: int, answer_pk: int):
        return self.client.get(
            reverse('forum:answer_accept', args=[question_pk, answer_pk]),
            follow=True)

    def delete_answer(self, question_pk: int, answer_pk: int):
        return self.client.post(
            reverse('forum:answer_delete', args=[question_pk, answer_pk]),
            follow=True)

    def delete_answer_confirmation_page(self, question_pk: int, answer_pk: int):
        return self.client.get(
            reverse('forum:answer_delete', args=[question_pk, answer_pk]),
            follow=True)

    def delete_question(self, question_pk: int):
        return self.client.post(
            reverse('forum:question_delete', args=[question_pk]),
            follow=True)

    def get_delete_question_confirmation_page(self, question_pk: int):
        return self.client.get(
            reverse('forum:question_delete', args=[question_pk]),
            follow=True)

    def delete_comment(self, question_pk: int, parent_model: str, comment_id: int):
        return self.client.get(
            reverse('forum:comment_delete', args=[question_pk, parent_model, comment_id]),
            follow=True)

    def follow_question(self, question_pk: int):
        return self.client.get(
            reverse('forum:follow', args=[question_pk]),
            follow=True, )

    def unfollow_question(self, question_pk: int):
        return self.client.get(
            reverse('forum:unfollow', args=[question_pk]),
            follow=True, )

    def upvote_comment(self, question_pk: int, parent_model: str, comment_id: int):
        return self.client.get(
            reverse('forum:comment_upvote', args=[question_pk, parent_model, comment_id]),
            follow=True, )

    def follow_tag(self, tag_word: str):
        return self.client.get(
            reverse('forum:watch_tag', args=[tag_word, ]),
            follow=True, )

    def unfollow_tag(self, tag_word: str):
        return self.client.get(
            reverse('forum:unwatch_tag', args=[tag_word, ]),
            follow=True, )

    def users_list(self):
        return self.client.get(reverse('userauth:list'), follow=True)

    def users_autocomplete(self, query: str):
        url = reverse('forum:users_autocomplete') + '?'
        if query is not None:
            url += f'q={query}'
        return self.client.get(url, follow=True)

    def invite_to_question_post(self, question_pk: int, invitee_usernames: str):
        return self.client.post(
            reverse('forum:invite', args=[question_pk]),
            {"usernames": invitee_usernames},
            follow=True)

    def invite_to_question_get(self, question_pk):
        return self.client.get(
            reverse('forum:invite', args=[question_pk]),
            follow=True)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f'admin:forum_{model}_changelist')
        if query is not None:
            url += f'?{query}'
        return self.client.get(url, follow=True)

    def admin_tag_changelist_post(self, model: str, data=None):
        url = reverse(f'admin:tags_{model}_changelist')
        return self.client.post(url, data, follow=True)

    def admin_change(self, model: str, pk: int):
        url = reverse(f'admin:forum_{model}_change', args=[pk, ])
        return self.client.get(url, follow=True)

    def bookmark_question(self, question_pk: int):
        url = reverse('forum:bookmark', args=[question_pk, ])
        return self.client.get(url, follow=True)

    def unbookmark_question(self, question_pk: int):
        url = reverse('forum:unbookmark', args=[question_pk, ])
        return self.client.get(url, follow=True)

    def mark_all_as_seen(self):
        return self.client.get(reverse('forum:mark_all_seen'), follow=True)

    def mark_as_seen(self, activity_pk: int):
        url = reverse('forum:mark_seen', args=[activity_pk, ])
        return self.client.get(url, follow=True)

    def view_partial_post_comments(self, post_type: str, post_pk: int):
        url = reverse('forum:post_comments', args=[post_type, post_pk])
        return self.client.get(url, follow=True)

    def view_partial_question_invites_get(self, question_pk: int, ):
        url = reverse('forum:questions_invites', args=[question_pk, ]) + '?'
        return self.client.get(url, follow=True)

    def articles_list(self, page=None, tab=None, query=None):
        url = reverse('articles:list') + '?'
        if page is not None:
            url += f'page={page}&'
        if tab is not None:
            url += f'tab={tab}&'
        if query is not None:
            url += f'q={query}&'
        return self.client.get(url, follow=True)

    def view_article_detail_get(self, article_pk: int):
        url = reverse('articles:detail', args=[article_pk, ]) + '?'
        return self.client.get(url, follow=True)

    def add_article_post(self, title: str, content: str, tags: str, **kwargs):
        url = reverse('articles:create')
        data = {'title': title,
                'articleeditor': content,
                'tags': tags,
                }
        return self.client.post(url, data, follow=True)

    def add_article_get(self):
        url = reverse('articles:create')
        return self.client.get(url, follow=True)

    def edit_article_get(self, article_pk: int):
        url = reverse('articles:edit', args=[article_pk, ])
        return self.client.get(url, follow=True)

    def edit_article_post(self, article_pk: int, title: str, content: str, tags: str):
        url = reverse('articles:edit', args=[article_pk, ])
        return self.client.post(url, {
            'title': title,
            'articleeditor': content,
            'tags': tags,
        }, follow=True)

    def delete_article(self, article_pk: int):
        return self.client.post(
            reverse('articles:delete', args=[article_pk]),
            follow=True)

    def delete_article_get(self, article_pk: int):
        return self.client.get(
            reverse('articles:delete', args=[article_pk]),
            follow=True)
