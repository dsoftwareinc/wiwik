from django.test import TestCase
from django.test import Client
from django.urls import reverse

# Create your tests here.
from userauth.models import ForumUser


class SpaceClient:
    def __init__(self):
        self.client = Client()

    def login(self, username: str, password: str):
        return self.client.login(username=username, password=password)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f'admin:spaces_{model}_changelist')
        if query is not None:
            url += f'?{query}'
        return self.client.get(url, follow=True)

    def admin_change(self, model: str, pk):
        url = reverse(f'admin:spaces_{model}_change', args=[pk, ])
        return self.client.get(url, follow=True)


class SpacesApiTestCase(TestCase):
    usernames = ['myuser_name1', 'myuser_name2', 'myuser_name3', ]
    password = 'magicalPa$$w0rd'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = [
            ForumUser.objects.create_user(
                username, f'{username}@a.com', cls.password,
            ) for username in cls.usernames]
