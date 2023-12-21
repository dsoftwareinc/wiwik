from django.urls import reverse

from articles.models import Article
from articles.tests.base import ArticlesApiTestCase
from common.test_utils import assert_url_in_chain
from forum.models import PostInvitation
from forum.views import utils
from userauth.models import ForumUser


class TestDeleteArticleView(ArticlesApiTestCase):
    users: list[ForumUser]
    title = "My article title"
    article_content = "My article content"
    tags = [
        "my_first_tag",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.article = utils.create_article(
            cls.users[0], cls.title, cls.article_content, ",".join(cls.tags)
        )

    def test_get_delete_article_confirmation_page__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        # act
        res = self.client.delete_article_get(self.article.pk)
        # assert
        self.assertEqual(1, Article.objects.all().count())
        self.assertEqual(
            reverse(
                "articles:delete",
                args=[
                    self.article.pk,
                ],
            ),
            res.request["PATH_INFO"],
        )

    def test_delete_article__green(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        utils.upvote(self.users[1], self.article)
        utils.upvote(self.users[2], self.article)
        question_user_previous_reputation = self.article.author.reputation_score
        # act
        res = self.client.delete_article(self.article.pk)
        # assert
        self.assertEqual(0, Article.objects.all().count())
        self.users[0].refresh_from_db()
        self.assertEqual(
            question_user_previous_reputation - 20, self.users[0].reputation_score
        )
        assert_url_in_chain(res, reverse("articles:list"))

    def test_delete_article__user_not_logged_in(self):
        # arrange
        # act
        res = self.client.delete_article(self.article.pk)
        # assert
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())
        assert_url_in_chain(
            res,
            reverse("userauth:login")
            + "?next="
            + reverse(
                "articles:delete",
                args=[
                    self.article.pk,
                ],
            ),
        )

    def test_delete_article__article_owned_by_different_user(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_article(self.article.pk)
        # assert
        assert_url_in_chain(res, reverse("articles:detail", args=[self.article.pk]))

    def test_delete_article__article_does_not_exist(self):
        # arrange
        self.client.login(self.usernames[1], self.password)
        # act
        res = self.client.delete_article(self.article.pk + 5)
        # assert
        self.assertEqual(404, res.status_code)

    def test_delete_article__article_has_invites__should_delete_invites(self):
        # arrange
        self.client.login(self.usernames[0], self.password)
        self.client.invite_to_question_post(
            self.article.pk,
            ",".join(
                [
                    self.usernames[2],
                ]
            ),
        )
        pk = self.article.pk
        # act
        res = self.client.delete_article(self.article.pk)
        # assert
        self.assertEqual(200, res.status_code)
        self.assertEqual(0, PostInvitation.objects.all().count())
        self.assertEqual(0, Article.objects.filter(pk=pk).count())
