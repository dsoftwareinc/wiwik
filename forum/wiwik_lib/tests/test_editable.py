import time
from datetime import timedelta

from django.test import Client, override_settings, TestCase
from django.urls import reverse

from common.test_utils import ForumClient, assert_message_in_response, assert_url_in_chain

from forum.views import utils
from userauth.models import ForumUser
from wiwik_lib.models import EditedResource


class EditableClient(ForumClient):
    def __init__(self):
        self.client = Client()

    def login(self, username: str, password: str):
        return self.client.login(username=username, password=password)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f'admin:wiwik_lib_{model}_changelist')
        if query is not None:
            url += f'?{query}'
        return self.client.get(url, follow=True)

    def admin_change(self, model: str, pk: int):
        url = reverse(f'admin:wiwik_lib_{model}_change', args=[pk, ])
        return self.client.get(url, follow=True)

    def edit_tag_get(self, tag_word: str):
        return self.client.get(reverse('tags:edit', args=[tag_word, ]), follow=True)

    def edit_tag_post(self, tag_word: str, description: str, wiki: str, summary: str):
        return self.client.post(
            reverse('tags:edit', args=[tag_word, ]),
            {'description': description, 'wiki': wiki, 'summary': summary, },
            follow=True, )


class EditableApiTestCase(TestCase):
    usernames = ['myusername1', 'myusername2', 'myusername3', ]

    password = 'magicalPa$$w0rd'
    title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    comment_content = 'comment---content'
    tags = ['my_first_tag', ]

    def setUp(self):
        self.client = EditableClient()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = [
            ForumUser.objects.create_user(
                item, f'{item}@a.com', cls.password,
                is_moderator=(item == cls.usernames[2]))
            for item in cls.usernames
        ]
        cls.question = utils.create_question(cls.users[0], cls.title, cls.question_content, ','.join(cls.tags))
        cls.answer = utils.create_answer(cls.answer_content, cls.users[1], cls.question)


class EditableTests(EditableApiTestCase):

    def test_edit_tag__second_edit_prevented(self):
        self.client.login(self.usernames[0], self.password)
        self.client.edit_tag_get(self.tags[0])
        self.client.login(self.usernames[1], self.password)
        #
        res = self.client.edit_tag_get(self.tags[0])
        #
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, f"Tag {self.tags[0]} is currently edited by a different user")
        assert_url_in_chain(res, reverse('tags:info', args=[self.tags[0], ]))

    @override_settings(EDIT_LOCK_TIMEOUT=timedelta(milliseconds=1))
    def test_edit_tag__first_edit_is_old(self):
        self.client.login(self.usernames[0], self.password)
        self.client.edit_tag_get(self.tags[0])
        self.client.login(self.usernames[2], self.password)
        time.sleep(0.01)
        #
        res = self.client.edit_tag_get(self.tags[0])
        #
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, EditedResource.objects.count())
        lock = EditedResource.objects.all()[0]
        self.assertEqual(lock.user, self.users[2])

    def test_edit_question__second_edit_prevented(self):
        self.client.login(self.usernames[0], self.password)
        self.client.edit_question_get(self.question.id)
        self.client.login(self.usernames[2], self.password)
        #
        res = self.client.edit_question_get(self.question.id)
        #
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "Question is currently edited by a different user")
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.id, ]))

    @override_settings(EDIT_LOCK_TIMEOUT=timedelta(milliseconds=1))
    def test_edit_question__first_edit_is_old(self):
        self.client.login(self.usernames[0], self.password)
        self.client.edit_question_get(self.question.id)
        self.client.login(self.usernames[2], self.password)
        time.sleep(0.01)
        #
        res = self.client.edit_question_get(self.question.id)
        #
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, EditedResource.objects.count())
        lock = EditedResource.objects.all()[0]
        self.assertEqual(lock.user, self.users[2])

    def test_edit_answer__second_edit_prevented(self):
        self.client.login(self.answer.author.username, self.password)
        self.client.edit_answer_get(self.answer.id)
        self.client.login(self.usernames[2], self.password)
        #
        res = self.client.edit_answer_get(self.answer.id)
        #
        self.assertEqual(200, res.status_code)
        assert_message_in_response(res, "Answer is currently edited by a different user")
        assert_url_in_chain(res, reverse('forum:thread', args=[self.question.id, ]))

    @override_settings(EDIT_LOCK_TIMEOUT=timedelta(milliseconds=1))
    def test_edit_answer__first_edit_is_old(self):
        self.client.login(self.answer.author.username, self.password)
        self.client.edit_answer_get(self.answer.id)
        self.client.login(self.usernames[2], self.password)
        time.sleep(0.01)
        #
        res = self.client.edit_answer_get(self.answer.id)
        #
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, EditedResource.objects.count())
        lock = EditedResource.objects.all()[0]
        self.assertEqual(lock.user, self.users[2])


class EditableAdminTest(EditableApiTestCase):
    superuser_name = 'superuser'
    password = 'magicalPa$$w0rd'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f'{cls.superuser_name}@a.com', cls.password)
        EditedResource.objects.create(user=cls.users[1], content_object=cls.question, )

    def setUp(self):
        super(EditableAdminTest, self).setUp()

    def test_admin_flags_changelist__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(1, EditedResource.objects.count())
        # act
        res = self.client.admin_changelist('editedresource')
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_flags_change__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(1, EditedResource.objects.count())
        # act
        res = self.client.admin_change('editedresource', EditedResource.objects.first().id)
        # assert
        self.assertEqual(200, res.status_code)
