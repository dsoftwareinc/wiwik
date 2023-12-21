import os

import urllib3
from django.core.files.base import ContentFile

from wiwik_lib.utils import ManagementCommand
from userauth.models import ForumUser

http = urllib3.PoolManager()


class Command(ManagementCommand):
    help = "Set password for admin and create users"

    def update_user_pic(self, user, force=False):
        self.print(f"Updating data for {user.email}")
        if os.path.isfile(user.profile_pic.path):
            self.print(f"User picture exists for {user.email} in {user.profile_pic.path}")
            if not force:
                return
        user_data = user.socialaccount_set.filter(provider="google").first()
        if user_data is None:
            self.error_print(f"No google user info for {user.email}")
            return
        user_data = user_data.extra_data
        picture_url = user_data.get("picture", None)
        if picture_url is None:
            self.error_print(f"No picture info in google data for user {user.email}")
            return
        req = http.request("GET", picture_url)
        data = ContentFile(req.data)
        file_name = f"profile_pic_{user.username}.google.jpeg"
        user.profile_pic.save(file_name, data, save=True)
        user.save()
        self.print(f"Profile pic for user {user.email} updated")

    def handle(self, *args, **options):
        user_qs = ForumUser.objects.all()
        for user in user_qs:
            self.update_user_pic(user)
