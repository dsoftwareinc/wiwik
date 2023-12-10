import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import CommandParser

from forum import models
from forum.views import notifications
from userauth.models import ForumUser
from wiwik_lib.models import Follow
from wiwik_lib.utils import ManagementCommand
from wiwik_lib.views.flag_views import notify_moderators_new_flag


class Command(ManagementCommand):
    base_dir: str
    originator: ForumUser
    """
    Generate sample emails in a directory
    """
    help = 'Generate sample emails in a directory'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('-d', '--dir', type=str, required=True, dest='directory',
                            help='Directory where to save the sample emails')

    def notify_moderators_new_flag(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'flags')
        question = models.Question.objects.all()[0]
        notify_moderators_new_flag(self.originator, question, 'question')

    def notify_new_comment(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'new_comment')
        comment = models.QuestionComment.objects.all()[0]
        notifications.notify_new_comment(self.originator, comment.get_question(), comment)

    def notify_answer_changes(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'answer_changes')
        answer = models.Answer.objects.all()[0]
        notifications.notify_answer_changes(self.originator, answer, 'old answer content')

    def notify_new_answer(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'new_answer')
        answer = models.Answer.objects.all()[0]
        notifications.notify_new_answer(self.originator, answer)

    def notify_question_changes(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'question_changes')
        content_type = ContentType.objects.get(app_label='forum', model='question')
        question = Follow.objects.filter(content_type=content_type)[0].content_object
        notifications.notify_question_changes(
            self.originator, question, 'Old title', 'Old content')

    def notify_tag_followers_new_question(self):
        settings.EMAIL_FILE_PATH = os.path.join(self.base_dir, 'new_question')
        tag_follow = models.UserTagStats.objects.filter(questions_by_user__gt=0).first()
        if tag_follow is None:
            self.error_print('No tag with followers, leaving notify_tag_followers_new_question')
            return
        question = tag_follow.tag.question_set.first()
        notifications.notify_tag_followers_new_question(
            self.originator, set(question.tag_words()), question)

    def handle(self, directory: str, *args, **options):
        """

        Args:
           directory (str): Directory where to save the files.
        """
        settings.SLACK_BOT_TOKEN = None
        settings.ALLOW_USER_NOTIFICATION_SKIPPING = False
        settings.EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
        self.base_dir = directory
        settings.RUN_ASYNC_JOBS_SYNC = True
        self.originator = ForumUser.objects.filter(is_superuser=True).first()
        if self.originator is None:
            self.error_print('No superuser in the system, can not send notifications')
        self.notify_moderators_new_flag()
        self.notify_new_comment()
        self.notify_answer_changes()
        self.notify_new_answer()
        self.notify_question_changes()
        self.notify_tag_followers_new_question()
