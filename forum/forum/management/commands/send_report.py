from datetime import date
from typing import List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import CommandParser
from django.utils import timezone
from django.utils.datetime_safe import datetime

from wiwik_lib.utils import ManagementCommand
from forum.management.tools import EmailType
from forum.reports import generate_report_html, tags_activity_email_report, \
    user_activity_email_report, recent_questions_email_report


class Command(ManagementCommand):
    """
    Generate reports from a specific date and either send them to emails
    or save them to file.
    """
    help = 'Send reports to emails or save to html file'
    report_types = {
        'tags_activity': tags_activity_email_report,
        'users_activity': user_activity_email_report,
        'questions': recent_questions_email_report,
    }
    report_options = ", ".join(report_types.keys())

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-f', '--fromdate', type=date.fromisoformat, required=True,
                            help='Report to include data from this date (YYYY-MM-DD)')
        parser.add_argument(
            '--reports', type=str, nargs='+', required=True,
            help=f'Reports to send, options: {self.report_options}')
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-e', '--emails', type=EmailType(), nargs='+',
                           help='emails to send report to')
        group.add_argument('--file', type=str,
                           help='Generate html file from report')

    def generate_reports(self, fromdate: date, report_names: List[str], ) -> List[str]:
        reports_list = list()
        for report_name in report_names:
            if report_name in self.report_types:
                reports_list.append(self.report_types[report_name](fromdate))
            else:
                self.error_print(f'Can not generate report of type "{report_name}"')
                self.error_print(f'Options are {self.report_options}')
                raise ValueError(f'Can not generate report of type "{report_name}"')
        return reports_list

    def handle(
            self, emails: List[str], file: str, fromdate: date, reports: List[str],
            *args, **options):
        """

        Args:
            emails (List[str]): emails to send report to
            file (str): filename to save to (if emails are empty)
            fromdate (date): date to check data from
            reports (List[str]): reports to include
        """
        fromdate = datetime.combine(fromdate, datetime.min.time(), )
        if settings.USE_TZ and timezone.is_naive(fromdate):
            fromdate = timezone.make_aware(fromdate)
        try:
            reports_list = self.generate_reports(fromdate, reports)
        except ValueError:
            return
        html = generate_report_html(
            f' Since you you last visited at {fromdate.date()}',
            reports_list,
            None,
        )

        if file:
            f = open(file, 'w')
            f.write(html)
            f.close()
        if emails:
            email = EmailMultiAlternatives(f'Activity on wiwik since {fromdate.date()}', '', to=emails)
            email.attach_alternative(html, "text/html")
            email.send()
