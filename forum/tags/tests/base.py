from django.test import Client, TestCase
from django.test.utils import override_settings
from django.urls import reverse

from forum.models import TagFollow
from tags.models import Tag
from userauth.models import ForumUser

number_of_questions = 30
max_answers = 5
max_comments = 3


class TagsClient:
    def __init__(self):
        self.client = Client()

    def login(self, username: str, password: str):
        return self.client.login(username=username, password=password)

    def home(self, page: int = None, tag_word: str = None):
        url = reverse('tags:list') + '?'
        if page is not None:
            url += f'page={page}&'
        if tag_word is not None:
            url += f'q={tag_word}&'
        return self.client.get(url, follow=True)

    def list_query(self, page: int = None, tag_word: str = None):
        url = reverse('tags:list_query') + '?'
        return self.client.get(url, follow=True)

    def edit_get(self, tag_word: str):
        return self.client.get(reverse('tags:edit', args=[tag_word, ]), follow=True)

    def info(self, tag_word: str):
        return self.client.get(reverse('tags:info', args=[tag_word, ]), follow=True)

    def edit_post(self, tag_word: str, description: str, wiki: str, summary: str):
        return self.client.post(
            reverse('tags:edit', args=[tag_word, ]), {
                'description': description,
                'wiki': wiki,
                'summary': summary,
            }, follow=True)

    def autocomplete(self, query: str):
        url = reverse('tags:autocomplete')
        if query is not None:
            url += '?q=' + query
        return self.client.get(url, follow=True)

    def synonyms_list_get(self, query: str = None, page: int = None, order_by: int = None):
        url = reverse('tags:synonyms_list') + '?'
        if query is not None:
            url += f'q={query}&'
        if page is not None:
            url += f'page={page}&'
        if order_by is not None:
            url += f'order_by={order_by}&'
        return self.client.get(url, follow=True)

    def synonyms_list_suggest(self, synonym: str, tag: str):
        url = reverse('tags:synonyms_list')
        return self.client.post(
            url, {'synonym': synonym, 'tag': tag, }, follow=True)

    def synonyms_approve(self, pk: int):
        url = reverse('tags:synonyms_approve', args=[pk, ])
        return self.client.get(url, follow=True)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f'admin:tags_{model}_changelist')
        if query is not None:
            url += f'?{query}'
        return self.client.get(url, follow=True)

    def admin_change(self, model: str, pk):
        url = reverse(f'admin:tags_{model}_change', args=[pk, ])
        return self.client.get(url, follow=True)


@override_settings(SKIP_USER_VISIT_LOG=True)
class TagsApiTestCase(TestCase):
    username = 'myusername'
    password = 'mySpecialPa$$Word'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = ForumUser.objects.create_user(cls.username, f'{cls.username}@a.com', cls.password)
        cls.tags = [Tag.objects.create(tag_word=f'tag{i}', description=f'tag{i}_desc') for i in range(3)]
        TagFollow.objects.create(tag=cls.tags[0], user=cls.user)

    def setUp(self):
        self.client = TagsClient()
