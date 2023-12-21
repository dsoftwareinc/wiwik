import textwrap
from io import StringIO
from unittest import mock

import fakeredis as fakeredis
from django.core.management import call_command
from django.test import TestCase
from redis import ResponseError
from scheduler.models import CronTask


class CreateCronJobsTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "create_cron_jobs",
            "--no-color",
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    @mock.patch("redis.Redis", return_value=fakeredis.FakeStrictRedis())
    def test__green(self, conn):
        prev_count = CronTask.objects.count()
        conn.info.side_effect = ResponseError()
        # act
        out = self.call_command()
        # assert
        self.assertEqual(prev_count + 6, CronTask.objects.count())
        self.assertEqual(
            textwrap.dedent(
                """\
            Creating CronJob: Daily activity report for admins
            Creating CronJob: Send users weekly digest
            Creating CronJob: Warn moderators about loosing status
            Creating CronJob: Moderator revoke/grant
            Creating CronJob: Calculate users impact
            Creating CronJob: Calculate badges for users
            """
            ),
            out,
        )
