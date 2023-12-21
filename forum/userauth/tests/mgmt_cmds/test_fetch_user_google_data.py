from io import StringIO

from django.core import management
from django.test import TestCase


class FetchGoogleDataTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        management.call_command(
            "fetch_user_google_data",
            "--no-color",
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    def test__green(self):
        # assert
        # act
        self.call_command()
        # assert
