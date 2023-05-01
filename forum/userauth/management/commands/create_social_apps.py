import os
import random

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from wiwik_lib.utils import ManagementCommand


def get_random_filename(path):
    filenames = os.listdir(path)
    return 'media/default_pics/' + random.choice(filenames)


class Command(ManagementCommand):
    help = 'Create instances for google connect'

    def _set_default_site_data(self) -> Site:
        site = Site.objects.all().first()
        site.domain = '127.0.0.1:8000'
        site.name = '127.0.0.1:8000'
        site.save()
        return site

    def _create_social_app(self, site: Site, name: str) -> None:
        """Create social app in the system.
        Parameters
        ----------
        site - site to create social app for
        name - name of social app, supported: okta, facebook, google

        """
        name = name.lower()
        if name not in {'google', 'okta', 'facebook'}:
            raise ValueError(f'social app {name} not supported')
        existing = SocialApp.objects.filter(provider=name).count()
        if existing > 0:
            self.print(f'{name} social app exists, skipping creation')
            return
        name_upcase = name.upper()
        client_id = os.getenv(f'{name_upcase}_CLIENT_ID', None)
        secret_key = os.getenv(f'{name_upcase}_SECRET_KEY', None)
        if client_id is None or secret_key is None:
            self.print(f'In order to setup google login, {name_upcase}_CLIENT_ID and '
                       f'{name_upcase}_SECRET_KEY should be set in the environment')
            return
        social_app = SocialApp.objects.create(
            provider=name,
            name=f'{name} Auth',
            client_id=client_id,
            secret=secret_key)
        social_app.sites.add(site)
        social_app.save()
        self.print(f'Added {name} auth to app')

    def handle(self, *args, **options):
        site = self._set_default_site_data()
        self._create_social_app(site, 'google')
        self._create_social_app(site, 'facebook')
        self._create_social_app(site, 'okta')
