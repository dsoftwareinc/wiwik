from django.apps import apps

from forum.tests.base import ForumApiTestCase
from forum.views import utils
from tags.models import Tag
from userauth.models import ForumUser
from wiwik_lib.views.flag_views import flag_model


class TestAdmin(ForumApiTestCase):
    superuser_name = 'superuser'
    password = 'magicalPa$$w0rd'
    question_title = 'my_question_title'
    question_content = 'my_question_content'
    answer_content = 'answer---content'
    comment_content = 'comment---content'
    tags = ['my_first_tag', 'my_second_tag', 'my_third_tag']

    MODELS_WITHOUT_ADMIN = {'questionview', 'questionadditionaldata'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser = ForumUser.objects.create_superuser(
            cls.superuser_name, f'{cls.superuser_name}@a.com', cls.password)
        cls.questions = [
            utils.create_question(user, cls.question_title, cls.question_content, ','.join(cls.tags))
            for user in cls.users
        ]
        cls.questions.extend([
            utils.create_question(user, cls.question_title, cls.question_content, cls.tags[0])
            for user in cls.users
        ])
        utils.create_answer(cls.answer_content, cls.users[0], cls.questions[0])
        utils.upvote(cls.users[0], cls.questions[1])
        utils.upvote(cls.users[0], cls.questions[2])
        utils.upvote(cls.users[1], cls.questions[0])
        utils.upvote(cls.users[1], cls.questions[2])
        a = utils.create_answer(cls.answer_content, cls.users[0], cls.questions[1])
        a.is_accepted = True
        a.question.has_accepted_answer = True
        a.save()
        a.question.save()
        utils.create_comment(cls.comment_content, cls.users[2], cls.questions[2])
        utils.create_comment(cls.comment_content, cls.users[1], a)
        flag_model(cls.users[2], cls.questions[0], 'spam')

    def test_admin_changelist__green(self):
        self.client.login(self.superuser_name, self.password)
        app_models = apps.all_models['forum'].keys()
        for model in app_models:
            if '_' in model or model in TestAdmin.MODELS_WITHOUT_ADMIN:
                continue
            res = self.client.admin_changelist(model)
            self.assertEqual(200, res.status_code, f'When testing for model {model}')

    def test_admin_change__green(self):
        self.client.login(self.superuser_name, self.password)
        app_models = apps.all_models['forum'].keys()
        for model in app_models:
            if '_' in model or model in TestAdmin.MODELS_WITHOUT_ADMIN:
                continue
            first = apps.get_model(f'forum.{model}').objects.all().first()
            if first:
                res = self.client.admin_change(model, first.id)
                self.assertEqual(200, res.status_code, f'When testing for model {model}')

    def test_admin_changelist__question_filter__green(self):
        self.client.login(self.superuser_name, self.password)

        res = self.client.admin_changelist('answer', query=f'question__id={self.questions[0].id}')
        self.assertEqual(200, res.status_code)

    def test_admin_answer_changelist__author_filter__green(self):
        self.client.login(self.superuser_name, self.password)

        res = self.client.admin_changelist('answer', query=f'author__username={self.usernames[0]}')
        self.assertEqual(200, res.status_code)

    def test_admin_tagfollow_changelist__tagname_filter__green(self):
        self.client.login(self.superuser_name, self.password)

        res = self.client.admin_changelist('tagfollow', query=f'tag__tag_word={self.tags[0]}')
        self.assertEqual(200, res.status_code)

    def test_admin_tag_changelist__merge_tags__green(self):
        self.client.login(self.superuser_name, self.password)
        q = self.questions[0]
        target_tag = Tag.objects.get(tag_word=self.tags[0])
        tag = Tag.objects.create(tag_word='tag-merge')
        q.tags.add(tag)
        q.save()
        data = {
            'action': 'merge_tags',
            '_selected_action': [tag.pk, target_tag.pk, ]
        }
        # act
        res = self.client.admin_tag_changelist_post('tag', data=data)

        # assert
        tag_refreshed = Tag.objects.filter(tag_word='tag-merge').first()
        q.refresh_from_db()
        self.assertIsNone(tag_refreshed)
        self.assertEqual(1, target_tag.synonym_set.count())
        self.assertEqual(set(self.tags), set(q.tag_words()))
