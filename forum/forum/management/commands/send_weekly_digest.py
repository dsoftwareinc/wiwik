from datetime import date, datetime
from typing import List

from django.core.mail import EmailMultiAlternatives
from django.core.management.base import CommandParser

from wiwik_lib.utils import ManagementCommand
from forum.jobs.reports_jobs import weekly_digest_to_user
from forum.management.tools import EmailType
from userauth.models import ForumUser


class Command(ManagementCommand):
    help = 'Send weekly digest report for user to emails or save it to a html file'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-f', '--fromdate', type=date.fromisoformat, required=True,
                            help='Report to include data from this date (YYYY-MM-DD)')
        parser.add_argument('--username', type=str, required=True,
                            help='Username in case you selected weekly_digest_to_user')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-e', '--emails', type=EmailType(), nargs='+',
                           help='emails to send report to')
        group.add_argument('--file', type=str,
                           help='Generate html file from report')

    def handle(self, emails: List[str], file: str, fromdate: date, username: str, *args, **options):
        fromdate = datetime.combine(fromdate, datetime.min.time(), )
        user = ForumUser.objects.filter(username=username).first()
        if user is None:
            self.error_print(f"User {username} not found")
            return
        html = weekly_digest_to_user(user, fromdate)
        if file:
            f = open(file, 'w')
            f.write(html)
            f.close()
        if emails:
            email = EmailMultiAlternatives(f'Weekly digest for user {username}', '', to=emails)
            email.attach_alternative(html, "text/html")
            email.send()
