from bs4 import BeautifulSoup
from django.urls import reverse

from common.test_utils import assert_message_in_response, assert_url_in_chain
from tags.models import Synonym
from tags.tests.base import TagsApiTestCase
from userauth.models import ForumUser


class TestSynonyms(TagsApiTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.synonyms = [
            Synonym.objects.create(
                name=f'synonym_{tag.tag_word}', tag=tag, active=False)
            for tag in cls.tags]

    def test_synonyms_list__green(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_get()
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))

    def test_synonyms_list__query__green(self):
        # arrange
        self.client.login(self.username, self.password)
        tag = self.tags[0]
        # act
        res = self.client.synonyms_list_get(query=tag.tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(2, len(soup.find_all('tr')))

    def test_synonyms_list__non_existing_page__returns_first_page(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_get(page=50)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))

    def test_synonyms_list__bad_order_by__returns_created_by(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_get(order_by='bad_value')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))

    def test_synonym_suggest__green(self):
        # arrange
        self.client.login(self.username, self.password)
        res = self.client.synonyms_list_get()
        soup = BeautifulSoup(res.content, 'html.parser')
        expected = len(soup.find_all('tr'))
        # act
        res = self.client.synonyms_list_suggest('synonym_suggestion', self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(expected + 1, len(soup.find_all('tr')))

    def test_synonym_suggest__empty_synonym__should_not_create(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_suggest("", self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))
        assert_message_in_response(res, 'Can not create empty synonym')

    def test_synonym_suggest__synonym_with_space__should_not_create(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_suggest('synonym name', self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))
        assert_message_in_response(res, 'Synonym name should not contain spaces')

    def test_synonym_suggest__non_existing_tag__should_not_create(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_suggest('synonymname', self.tags[0].tag_word + '111')
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))
        assert_message_in_response(res, 'Could not find this tag, first ask a few questions with it')

    def test_synonym_suggest__synonym_name_exist__should_not_create(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_suggest(self.synonyms[0].name, self.tags[0].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))
        assert_message_in_response(res, 'Synonym with this name already suggested for this tag, aborting')

    def test_synonym_suggest__synonym_name_exist_for_another_tag__should_not_create(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_list_suggest(self.synonyms[0].name, self.tags[1].tag_word)
        # assert
        self.assertEqual(200, res.status_code)
        soup = BeautifulSoup(res.content, 'html.parser')
        self.assertEqual(len(self.synonyms) + 1, len(soup.find_all('tr')))
        assert_message_in_response(res, 'Synonym with this name already suggested for another tag, aborting')


class TestSynonymsApproval(TagsApiTestCase):
    moderator_name = 'moderator'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.moderator = ForumUser.objects.create_user(
            cls.moderator_name,
            f'{cls.moderator_name}@a.com',
            cls.password,
            is_moderator=True,
        )
        cls.synonyms = [
            Synonym.objects.create(
                name=f'synonym_{tag.tag_word}', tag=tag, active=False)
            for tag in cls.tags]

    def test_synonym_approve__green(self):
        # arrange
        self.client.login(self.moderator_name, self.password)
        # act
        res = self.client.synonyms_approve(self.synonyms[0].id)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('tags:synonyms_list'))
        self.synonyms[0].refresh_from_db()
        self.assertTrue(self.synonyms[0].active)

    def test_synonym_approve__non_existing_synonym__do_nothing(self):
        # arrange
        self.client.login(self.moderator_name, self.password)
        # act
        res = self.client.synonyms_approve(len(self.synonyms) + 10)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('tags:synonyms_list'))

    def test_synonym_approve__non_moderator__do_nothing(self):
        # arrange
        self.client.login(self.username, self.password)
        # act
        res = self.client.synonyms_approve(self.synonyms[0].id)
        # assert
        self.assertEqual(200, res.status_code)
        assert_url_in_chain(res, reverse('tags:synonyms_list'))
