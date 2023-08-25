import os
import random

from django.conf import settings

from wiwik_lib.utils import ManagementCommand
from userauth.models import ForumUser


def get_random_filename(path):
    filenames = os.listdir(os.path.join(settings.MEDIA_ROOT, path))
    return os.path.join(path, random.choice(filenames))


class Command(ManagementCommand):
    help = 'Set password for admin and create users'

    def handle(self, *args, **options):
        number_of_users = 10
        try:
            ForumUser.objects.create_superuser('admin', 'a@a.com', '1111')
        except Exception as e:  # noqa: F841
            self.print('Could not create admin')

        for i in range(number_of_users):
            profile_pic = get_random_filename('default_pics')
            try:
                ForumUser.objects.create_user(f'user{i}',
                                              f'user{i}@so.com',
                                              f'user{i}',
                                              name=f'user name {i}',
                                              title='fancy title',
                                              profile_pic=profile_pic
                                              )
            except Exception as e:  # noqa: F841
                self.print(f'Could not create user{i}')
