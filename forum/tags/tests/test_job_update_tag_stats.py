from tags import jobs
from tags.models import Tag
from tags.tests.base import TagsApiTestCase


class TestJobUpdateTagStates(TagsApiTestCase):
    def test_update_tag_stats__green(self):
        # act
        jobs.update_tag_stats()
        # assert
        tags = Tag.objects.all()
        for tag in tags:
            self.assertEqual(0, tag.number_asked_today)
            self.assertEqual(0, tag.number_of_questions)
            self.assertEqual(0, tag.number_asked_this_week)
