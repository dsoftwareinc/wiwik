from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, tag


@tag("management_command")
class SendReportTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        call_command(
            "send_report",
            "--no-color",
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    @mock.patch("builtins.open", create=True)
    def test__all_reports_to_file__green(self, file_mock: mock.MagicMock):
        params = "-f 2020-01-01 --reports tags_activity users_activity questions --file x.html"
        # act
        out = self.call_command(params.split(" "))
        # assert
        self.assertEqual("", out)
        file_mock.assert_called_with("x.html", "w")

    def test__all_reports_to_email__green(self):
        params = (
            "-f 2020-01-01 --reports tags_activity users_activity questions -e a@a.com"
        )
        # act
        out = self.call_command(params.split(" "))
        # assert
        self.assertEqual("", out)

    def test__none_existing_report__should_exit(self):
        params = "-f 2020-01-01 --reports bad_report -e a@a.com"
        # act
        out = self.call_command(params.split(" "))
        # assert
        self.assertEqual(
            'Can not generate report of type "bad_report"\n'
            "Options are tags_activity, users_activity, questions\n",
            out,
        )
