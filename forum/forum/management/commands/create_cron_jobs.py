from scheduler.models import Task, TaskType

from wiwik_lib.utils import ManagementCommand


class Command(ManagementCommand):
    help = "Create basic cron jobs on environment"

    def create_job(self, name: str, callable_method: str, cron_str: str):
        self.print(f"Creating CronJob: {name}")
        exists = Task.objects.filter(callable=callable_method).first()
        if exists is not None:
            self.error_print(f"Job with callable {callable_method} exists, skipping")
            return
        Task.objects.create(
            name=name,
            task_type=TaskType.CRON,
            callable=callable_method,
            queue="cron",
            cron_string=cron_str,
        )

    def handle(self, *args, **options):
        self.create_job(
            "Daily activity report for admins",
            "forum.jobs.send_daily_activity_report_for_admins",
            "0 0 * * 2-6",
        )
        self.create_job(
            "Send users weekly digest",
            "forum.jobs.send_weekly_digest_for_users",
            "0 0 * * 1",
        )
        self.create_job(
            "Warn moderators about loosing status",
            "forum.jobs.warn_users_loosing_moderator_status",
            "0 0 15 * *",
        )
        self.create_job(
            "Moderator revoke/grant",
            "forum.jobs.update_moderator_status_for_users",
            "0 0 1 * *",
        )
        self.create_job(
            "Calculate users impact",
            "forum.jobs.calculate_all_users_impact",
            "0 0 * * *",
        )
        self.create_job("Calculate badges for users", "badges.jobs.review_all_badges", "0 */3 * * *")
