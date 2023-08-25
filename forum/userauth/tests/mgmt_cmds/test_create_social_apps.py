import os
from io import StringIO

from allauth.socialaccount.models import SocialApp
from django.core import management
from django.test import TestCase


class CreateSocialAppsTest(TestCase):
    def call_command(self, *args, **kwargs):
        out = StringIO()
        management.call_command(
            "create_social_apps",
            '--no-color',
            *args,
            **kwargs,
            stdout=out,
            stderr=StringIO(),
        )
        return out.getvalue()

    def test__green(self):
        # arrange
        os.environ['GOOGLE_CLIENT_ID'] = 'x'
        os.environ['GOOGLE_SECRET_KEY'] = 'x'
        os.environ['FACEBOOK_CLIENT_ID'] = 'x'
        os.environ['FACEBOOK_SECRET_KEY'] = 'x'
        os.environ['OKTA_BASE_URL'] = 'x'
        os.environ['OKTA_CLIENT_ID'] = 'x'
        os.environ['OKTA_SECRET_KEY'] = 'x'
        # act
        out = self.call_command()
        # assert
        self.assertEqual(3, SocialApp.objects.count())
        self.assertEqual('Added google auth to app\nAdded facebook auth to app\nAdded okta auth to app\n', out)
