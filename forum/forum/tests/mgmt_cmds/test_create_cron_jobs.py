import textwrap
from io import StringIO
from unittest import mock

import fakeredis
from django.core.management import call_command
from django.test import TestCase
from redis import ResponseError
from scheduler.models import Task, TaskType


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

    @mock.patch("scheduler.helpers.queues.getters._get_connection", return_value=fakeredis.FakeStrictRedis())
    def test__green(self, conn):
        prev_count = Task.objects.filter(task_type=TaskType.CRON).count()
        conn.info.side_effect = ResponseError()
        # act
        out = self.call_command()
        # assert
        self.assertEqual(prev_count + 6, Task.objects.filter(task_type=TaskType.CRON).count())
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
