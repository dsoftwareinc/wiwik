from tags.models import Synonym, TagEdit
from tags.tests.base import TagsApiTestCase
from userauth.models import ForumUser


class TagAdminTest(TagsApiTestCase):
    superuser_name = "superuser"
    password = "magicalPa$$w0rd"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f"{cls.superuser_name}@a.com", cls.password
        )
        cls.synonyms = [
            Synonym.objects.create(
                name=f"synonym_{tag.tag_word}", tag=tag, active=False
            )
            for tag in cls.tags
        ]
        cls.tagedit = TagEdit.objects.create(
            tag=cls.tags[0],
            author=cls.superuser,
            summary="edit_summary",
            before_wiki="tag.wiki",
            before_description="tag.description",
        )

    def test_admin_tag_changelist__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("tag")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_tag_changelist__query__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("tag", query="tag1")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_tag_single_view__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_change("tag", self.tags[0].id)
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_synonym_changelist__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("synonym")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_synonym_single_view__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_change("synonym", self.synonyms[0].id)
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_tagedit_changelist__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_changelist("tagedit")
        # assert
        self.assertEqual(200, res.status_code)

    def test_admin_tagedit_single_view__green(self):
        # arrange
        self.client.login(self.superuser_name, self.password)
        # act
        res = self.client.admin_change("tagedit", self.tagedit.id)
        # assert
        self.assertEqual(200, res.status_code)
