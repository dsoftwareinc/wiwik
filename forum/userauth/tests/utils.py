from django.test import Client
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from forum.models import Question
from forum.views.utils import create_question
from userauth import models
from userauth.models import ForumUser
from userauth.views.tokens import account_activation_token


class UserAuthClient(Client):
    def signup_and_login(self, username, fullname, email, password):
        self.signup_post(username, fullname, email, password)
        user = models.ForumUser.objects.get(username=username)
        user_id_base64 = urlsafe_base64_encode(force_bytes(user.pk))
        activation_key = account_activation_token.make_token(user)
        self.activate_user(user_id_base64, activation_key)
        self.login(username, password)

    def signup_get(self):
        return self.get(reverse("userauth:signup"), follow=True)

    def signup_post(
        self, username: str, name: str, email: str, password: str, password2: str = None
    ):
        return self.post(
            reverse("userauth:signup"),
            data={
                "username": username,
                "name": name,
                "email": email,
                "password1": password,
                "password2": password2 if password2 is not None else password,
            },
            follow=True,
        )

    def login(self, username: str, password: str):
        return super().login(username=username, password=password)

    def login_get(self):
        return self.get(reverse("userauth:login"), follow=True)

    def login_post(self, username: str, password: str, next_url: str = None):
        url = reverse("userauth:login") + "?"
        if next_url:
            url += f"next={next_url}&"
        return self.post(
            url,
            data={
                "username": username,
                "password": password,
            },
            follow=True,
        )

    def logout_get(self):
        return self.get(reverse("userauth:logout"), follow=True)

    def activate_user(self, user_id_base64, activation_key):
        return self.get(
            reverse("userauth:activate", args=[user_id_base64, activation_key]),
            follow=True,
        )

    def unsubscribe(self, user_id_base64, activation_key):
        return self.get(
            reverse("userauth:unsubscribe", args=[user_id_base64, activation_key]),
            follow=True,
        )

    def view_profile(self, username, tab, page=None):
        url = reverse("userauth:profile", args=[username, tab]) + "?"
        if page is not None:
            url += f"page={page}&"
        return self.get(url, follow=True)

    def view_user_navbar(self):
        url = reverse("forum:user_navbar") + "?"

        return self.get(url, follow=True)

    def staff_deactivate_user(self, username: str):
        url = (
            reverse(
                "userauth:deactivate_user",
                args=[
                    username,
                ],
            )
            + "?"
        )
        return self.get(url, follow=True)

    def staff_activate_user(self, username: str):
        url = (
            reverse(
                "userauth:activate_user",
                args=[
                    username,
                ],
            )
            + "?"
        )
        return self.get(url, follow=True)

    def edit_profile_get(self):
        return self.get(
            reverse("userauth:edit"),
            follow=True,
        )

    def edit_profile_post(
        self, fullname: str, title: str, about: str, email_notifications: str
    ):
        data = {
            "fullname": fullname,
            "title": title,
            "about": about,
        }
        if email_notifications is not None:
            data["email_notifications"] = email_notifications
        return self.post(reverse("userauth:edit"), data=data, follow=True)

    def profile_pic_post(self, image_data: str):
        return self.post(
            reverse("userauth:profile_pic"), data={"cropped-profile-pic": image_data}
        )

    def profile_pic_get(self):
        return self.get(reverse("userauth:profile_pic"))

    def users_list_query(self, tab: str = "all", **kwargs):
        url = reverse("userauth:list_query") + f"?tab={tab}&"
        user = kwargs.get("user", None)
        if user:
            url += f"q={user}&"
        page = kwargs.get("page", None)
        if page:
            url += f"page={page}&"
        return self.get(url, follow=True)

    def users(self, tab: str = "all", **kwargs):
        url = reverse("userauth:list") + f"?tab={tab}&"
        from_date = kwargs.get("from_date", None)
        if from_date:
            url += f"from_date={from_date}&"
        user = kwargs.get("user", None)
        if user:
            url += f"q={user}&"
        page = kwargs.get("page", None)
        if page:
            url += f"page={page}&"
        return self.get(url, follow=True)

    def admin_change(self, model: str, pk):
        url = reverse(
            f"admin:userauth_{model}_change",
            args=[
                pk,
            ],
        )
        return self.get(url, follow=True)

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f"admin:userauth_{model}_changelist")
        if query is not None:
            url += f"?{query}"
        return self.get(url, follow=True)

    def admin_changelist_post(self, model: str, data=None):
        url = reverse(f"admin:userauth_{model}_changelist")
        return self.post(url, data, follow=True)

    def send_email_post(self, users: list[int], subject: str, message: str):
        data = {
            "users": users,
            "subject": subject,
            "message": message,
        }
        return self.post(reverse("userauth:admin_email"), data, follow=True)


@override_settings(SKIP_USER_VISIT_LOG=True)
class UserAuthTestCase(TestCase):
    users: list[ForumUser]
    question: Question
    usernames = [
        "myuname1",
        "myuname2",
        "diff_username",
    ]
    password = "magicalPa$$w0rd"
    tabs = (
        "questions",
        "answers",
        "votes",
        "reputation",
        "following",
        "bookmarks",
        "badges",
    )
    title = "my_question_title"
    question_content = "my_question_content_with more than 20 chars"
    tags = [
        "my_first_tag",
        "second_tag",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = [
            ForumUser.objects.create_user(username, f"{username}@a.com", cls.password)
            for username in cls.usernames
        ]
        cls.question = create_question(
            cls.users[0], cls.title, cls.question_content, ",".join(cls.tags)
        )

    def setUp(self):
        self.client = UserAuthClient()
