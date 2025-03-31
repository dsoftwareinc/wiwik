from datetime import timedelta

from django.utils import timezone
from scheduler import job

from forum.models import QuestionView


@job()
def purge_question_views(delta: timedelta):
    starting_datetime = timezone.now() - delta
    QuestionView.objects.filter(created_at__lt=starting_datetime).delete()
