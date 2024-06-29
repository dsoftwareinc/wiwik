from constance import config

from forum import models
from forum.tests.base import ForumApiTestCase
from forum.views import utils, follow_models


class TestForumTagPopover(ForumApiTestCase):
    tags = ["my_first_tag", "my_second_tag"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        num_users = len(cls.users)
        for i in range(config.QUESTIONS_PER_PAGE + 2):
            utils.create_question(
                cls.users[i % num_users],
                cls.title,
                cls.question_content,
                ",".join(cls.tags),
            )

    def test_tag_popover__tags_with_experts_and_stars__should_show_in_popover(self):
        # arrange
        tag_description = "my tag description with many things"
        self.client.login(self.usernames[1], self.password)
        user = self.users[1]
        tags_list = list()
        for i in range(3):
            tag = models.Tag.objects.create(tag_word=f"tag{i}", description=tag_description)
            follow_models.create_follow_tag(tag, user)
            tags_list.append(tag)
        tag_str = ",".join([f"tag{i}" for i in range(3)])
        utils.create_question(user, self.title, self.question_content, tag_str)
        for tag in tags_list:
            tag.experts = self.usernames[2]
            tag.stars = self.usernames[2]
            tag.save()

        for tag in tags_list:
            # act
            res = self.client.view_partial_tag_popover(tag.pk)
            # assert
            self.assertContains(res, tag.tag_word)
            self.assertContains(res, tag_description)
            self.assertContains(res, "Leaders:")
            self.assertContains(res, "stars:")
            self.assertContains(res, self.usernames[2])
