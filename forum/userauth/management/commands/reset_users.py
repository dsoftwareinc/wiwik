import os
import random

from django.conf import settings


from userauth.apps import logger
from userauth.management.wordlists import get_random_username
from userauth.models import ForumUser
from wiwik_lib.utils import ManagementCommand


class Command(ManagementCommand):
    help = 'Reset user password and image'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password', type=str, nargs='?', default='1111',
            help='password to set to')

    def handle(self, password='1111', *args, **options):
        users = ForumUser.objects.all()
        logger.info(f'{users.count()} users found')
        filenames = os.listdir(os.path.join(settings.MEDIA_ROOT, 'default_pics'))
        for user in users:
            user.set_password(password)
            user.name = get_random_username()
            profile_pic_filename = 'default_pics/' + random.choice(filenames)
            user.profile_pic = profile_pic_filename
            logger.info(f'Resetting password and profile-pic for {user.username}: using {profile_pic_filename}')
            user.save()
