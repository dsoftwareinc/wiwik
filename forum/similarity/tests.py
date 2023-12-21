from io import StringIO
from unittest.mock import MagicMock, call

from django.conf import settings
from django.core.management import call_command
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from forum.models import Question
from forum.views import utils
from similarity import algo, models
from similarity.calculate_similarity_job import (
    calculate_similarity_for_question,
    calculate_tfidf,
)
from similarity.models import PostSimilarity
from similarity.views import most_similar_questions_by_postgres_rank
from userauth.models import ForumUser


class TestBase(TestCase):
    usernames = [
        "myuser_name1",
        "myuser_name2",
        "myuser_name3",
    ]
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"
    question_title = "my_question_title"
    question_content = "my_question_content"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )
        cls.users = [ForumUser.objects.create_user(item, f"{item}@a.com", cls.password) for item in cls.usernames]
        cls.questions = [
            utils.create_question(user, cls.question_title, cls.question_content, "") for user in cls.users
        ]

    def setUp(self) -> None:
        self.client = Client()


class TestSimilarity(TestBase):
    def test_admin_similarity_change_list__green(self):
        # arrange
        for q1 in self.questions:
            for q2 in self.questions:
                if q1.id < q2.id:
                    PostSimilarity.objects.create(
                        question1=q1,
                        question2=q2,
                        tfidf_rank=0.1,
                        postgres_rank=0.9,
                        postgres_trigram_rank=0.5,
                        rank=0,
                    )
        num_similarities = PostSimilarity.objects.count()
        self.client.login(username=self.superuser_name, password=self.password)
        # act
        res = self.client.get(reverse("admin:similarity_postsimilarity_changelist"))
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, f"{num_similarities} selected")

    def test_admin_similarity_change__green(self):
        # arrange
        sim = PostSimilarity.objects.create(
            question1=self.questions[0],
            question2=self.questions[1],
            tfidf_rank=0.1123,
            postgres_rank=0.9323,
            postgres_trigram_rank=0.5323,
            rank=0,
        )
        url = reverse(
            "admin:similarity_postsimilarity_change",
            args=[
                sim.pk,
            ],
        )
        self.client.login(username=self.superuser_name, password=self.password)
        # act
        res = self.client.get(url)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertContains(res, sim.__str__())

    def test_get_similarity(self):
        for q1 in self.questions:
            for q2 in self.questions:
                if q1.id < q2.id:
                    PostSimilarity.objects.create(
                        question1=q1,
                        question2=q2,
                        rank=0,
                        tfidf_rank=0.1,
                        postgres_rank=0.9,
                        postgres_trigram_rank=0.5,
                    )
        # act
        res = most_similar_questions_by_postgres_rank(self.questions[0], count=2)
        # assert
        self.assertEqual(2, len(res))
        self.assertNotIn(self.questions[0], res)

    def test_calculate_similarity_pair__green(self):
        # arrange
        settings.DATABASES["default"]["ENGINE"] = "django.db.backends.postgresql"
        algo.postgres_search_rank = MagicMock()
        algo.postgres_search_rank.side_effect = [0.5, 0.1]
        algo.postgres_trigram_rank = MagicMock()
        algo.postgres_trigram_rank.side_effect = [0.5, 0.1]
        # act
        calculate_similarity_for_question(self.questions[0])
        # assert
        calls = []
        for q in self.questions:
            if q != self.questions[0]:
                calls.append(call(self.questions[0].title, q))
        algo.postgres_search_rank.assert_has_calls(calls, any_order=True)


class TestTfIdf(TestBase):
    def test__tfidf__green(self):
        # act
        calculate_tfidf()
        # assert
        question_count = Question.objects.count()
        self.assertEqual(question_count * (question_count - 1) / 2, PostSimilarity.objects.count())


class TestCalculateSimilarities(TestCase):
    usernames = [
        "myuser_name1",
        "myuser_name2",
    ]
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"
    question_title = "my_question_title"
    question_content = "my_question_content"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )
        cls.users = [ForumUser.objects.create_user(item, f"{item}@a.com", cls.password) for item in cls.usernames]
        cls.questions = [
            utils.create_question(user, cls.question_title, cls.question_content, "") for user in cls.users
        ]

    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "calculate_similarities",
            *args,
            stdout=out,
            stderr=StringIO(),
            **kwargs,
        )
        return out.getvalue()

    def test__green(self):
        # act
        out = self.call_command()
        # assert
        self.assertEqual("", out)
        self.assertEqual(1, models.PostSimilarity.objects.count())
