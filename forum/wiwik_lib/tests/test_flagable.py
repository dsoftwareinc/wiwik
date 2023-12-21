from unittest import mock

from django.test import Client
from django.test import TestCase
from django.urls import reverse

from common.test_utils import assert_message_in_response, assert_url_in_chain
from forum import jobs, models
from forum.integrations import slack_api
from forum.views import utils
from userauth.models import ForumUser
from wiwik_lib.models import Flag
from wiwik_lib.views.flag_views import flag_model


class FlagsClient:
    def __init__(self):
        self.client = Client()

    def login(self, username: str, password: str):
        return self.client.login(username=username, password=password)

    def flag_model(
        self, model_name: str, model_pk: int, flag_type: str, extra: str = None
    ):
        data = {
            "model-name": model_name,
            "model_pk": model_pk,
            "flag_type": flag_type,
        }
        if extra is not None:
            data["extra"] = extra
        url = reverse("general:flag_create", args=[model_pk])
        return self.client.post(
            url,
            data,
            follow=True,
        )

    def admin_changelist(self, model: str, query: str = None):
        url = reverse(f"admin:wiwik_lib_{model}_changelist")
        if query is not None:
            url += f"?{query}"
        return self.client.get(url, follow=True)

    def admin_change(self, model: str, pk: int):
        url = reverse(
            f"admin:wiwik_lib_{model}_change",
            args=[
                pk,
            ],
        )
        return self.client.get(url, follow=True)


class FlagApiTestCase(TestCase):
    usernames = [
        "myusername1",
        "myusername2",
        "myusername3",
    ]

    password = "magicalPa$$w0rd"
    title = "my_question_title"
    question_content = "my_question_content"
    answer_content = "answer---content"
    comment_content = "comment---content"
    tags = [
        "my_first_tag",
    ]

    def setUp(self):
        self.client = FlagsClient()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.users = [
            ForumUser.objects.create_user(
                item,
                f"{item}@a.com",
                cls.password,
                is_moderator=(item == cls.usernames[2]),
            )
            for item in cls.usernames
        ]
        cls.question = utils.create_question(
            cls.users[0], cls.title, cls.question_content, ",".join(cls.tags)
        )
        a = utils.create_answer(cls.answer_content, cls.users[1], cls.question)
        cls.question_pk = cls.question.pk
        cls.answer_pk = a.pk
        cls.qcomment = utils.create_comment(
            cls.comment_content, cls.users[2], cls.question
        )
        cls.acomment = utils.create_comment(cls.comment_content, cls.users[0], a)
        cls.qcomment_pk = cls.qcomment.pk
        cls.acomment_pk = cls.acomment.pk


class TestFlagAnswerView(FlagApiTestCase):
    @mock.patch("forum.jobs.start_job")
    def test_flag_answer__green(self, start_job: mock.MagicMock):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.flag_model("answer", self.answer_pk, "spam")
        # assert
        answer = models.Answer.objects.get(pk=self.answer_pk)
        self.assertEqual(1, answer.flags.count())
        message = "Successfully flagged this answer."
        assert_message_in_response(res, message)
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question_pk])
            + f"#answer_{self.answer_pk}",
        )
        start_job.assert_has_calls(
            [
                mock.call(
                    jobs.notify_user_email,
                    self.users[2],
                    mock.ANY,
                    mock.ANY,
                    mock.ANY,
                    True,
                ),
                mock.call(
                    slack_api.slack_post_im_message_to_email,
                    mock.ANY,
                    self.users[2].email,
                ),
            ]
        )

    def test_flag_answer__same_user__should_do_nothing(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("answer", self.answer_pk, "spam")
        # assert
        answer = models.Answer.objects.get(pk=self.answer_pk)
        self.assertEqual(0, answer.flags.count())
        message = "You cannot flag your own answer."
        assert_message_in_response(res, message)

    def test_flag_answer__already_flagged__should_do_nothing(self):
        answer = models.Answer.objects.get(pk=self.answer_pk)
        flag_model(self.users[0], answer, "spam")
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.flag_model("answer", self.answer_pk, "spam")
        # assert
        message = "You already flagged this answer."
        self.assertEqual(1, answer.flags.count())
        assert_message_in_response(res, message)


class TestFlagCommentView(FlagApiTestCase):
    def test_flag_comment_for_question__green(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.flag_model("comment_question", self.qcomment_pk, "rude")
        # assert
        self.assertEqual(1, Flag.objects.count())
        flag = Flag.objects.all().first()
        self.assertEqual(self.qcomment_pk, flag.object_id)
        message = "Successfully flagged this comment."
        assert_message_in_response(res, message)
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question_pk])
            + f"#question_{self.question_pk}",
        )

    def test_flag_comment_for_answer__green(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("comment_answer", self.acomment_pk, "spam")
        # assert
        comment = models.AnswerComment.objects.get(pk=self.acomment_pk)
        self.assertEqual(1, comment.flags.count())
        message = "Successfully flagged this comment."
        assert_message_in_response(
            res,
            message,
        )
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question_pk])
            + f"#answer_{self.answer_pk}",
        )

    def test_flag_comment_for_answer__same_user__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.flag_model("comment_answer", self.acomment_pk, "spam")
        # assert
        comment = models.AnswerComment.objects.get(pk=self.acomment_pk)
        self.assertEqual(0, comment.flags.count())
        message = "You cannot flag your own comment."
        assert_message_in_response(res, message)

    def test_flag_comment_for_answer__already_flagged__should_do_nothing(self):
        comment = models.AnswerComment.objects.get(pk=self.acomment_pk)
        flag_model(self.users[1], comment, "spam")
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("comment_answer", self.acomment_pk, "spam")
        # assert
        message = "You already flagged this comment."
        assert_message_in_response(res, message)
        self.assertEqual(1, comment.flags.count())


class TestFlagQuestionView(FlagApiTestCase):
    def test_flag_question__green(self):
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("question", self.question.pk, "spam")
        # assert
        self.question.refresh_from_db()
        self.assertEqual(1, self.question.flags.count())
        message = "Successfully flagged this question."
        assert_message_in_response(res, message)
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#question_{self.question.pk}",
        )

    def test_flag_question__same_user__should_do_nothing(self):
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.flag_model("question", self.question.pk, "spam")
        # assert
        comment = models.AnswerComment.objects.get(pk=self.acomment.pk)
        self.assertEqual(0, comment.flags.count())
        message = "You cannot flag your own question."
        assert_message_in_response(res, message)

    def test_flag_question__already_flagged_by_same_user__should_do_nothing(self):
        question = models.Question.objects.get(pk=self.question.pk)
        flag_model(self.users[1], question, "spam")
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("question", self.question.pk, "spam")
        # assert
        message = "You already flagged this question."
        assert_message_in_response(res, message)
        self.assertEqual(1, question.flags.count())

    def test_flag_question__already_flagged_by_another_user__should_flag(self):
        question = models.Question.objects.get(pk=self.question.pk)
        flag_model(self.users[2], question, "spam")
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.flag_model("question", self.question.pk, "spam")
        # assert
        self.question.refresh_from_db()
        self.assertEqual(2, self.question.flags.count())
        message = "Successfully flagged this question."
        assert_message_in_response(res, message)
        assert_url_in_chain(
            res,
            reverse("forum:thread", args=[self.question.pk])
            + f"#question_{self.question.pk}",
        )

    def test_flag_question__bad_request__do_nothing(self):
        self.client.login(self.usernames[1], self.password)
        url = reverse("general:flag_create", args=[self.question.pk])
        res = self.client.client.get(url, follow=True)
        # assert
        self.assertEqual(400, res.status_code)

    def test_flag_question__non_existing_model__green(self):
        self.client.login(self.usernames[1], self.password)
        # act
        self.client.flag_model("question", self.question.pk + 6, "spam")
        # assert
        self.question.refresh_from_db()
        self.assertEqual(0, self.question.flags.count())


class FlagsAdminTest(FlagApiTestCase):
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )
        Flag.objects.create(
            user=cls.users[1],
            flag_type="rude",
            content_object=cls.question,
            content_author=cls.question.author,
        )

    def setUp(self):
        super(FlagsAdminTest, self).setUp()

    def test_admin_flags_changelist__green(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        self.client.login(self.superuser_name, self.password)
        self.client.flag_model("question", self.question.pk, "spam")
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(2, Flag.objects.count())
        # act
        res = self.client.admin_changelist("flag")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_flags_change__green(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        self.client.login(self.superuser_name, self.password)
        self.client.flag_model("question", self.question.pk, "spam")
        self.client.login(self.superuser_name, self.password)
        self.assertEqual(2, Flag.objects.count())
        # act
        res = self.client.admin_change("flag", Flag.objects.first().id)
        # assert
        self.assertEqual(200, res.status_code)
