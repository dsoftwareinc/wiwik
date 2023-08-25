from io import StringIO

from django.core.management import call_command
from django.test import TestCase, tag

from tags.models import Tag


@tag('management_command')
class CalculateTagFollowStatsTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "calculate_tag_follow_stats",
            '--no-color',
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tags = [Tag.objects.create(tag_word=f'tag{i}', description=f'tag{i}_desc') for i in range(3)]

    def test__green(self):
        # act
        out = self.call_command()
        # assert
        self.assertEqual('', out)
