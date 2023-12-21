from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from scheduler import job

from forum.models import Question, Answer, VoteActivity
from userauth.models import ForumUser


@job
def calculate_user_impact(user: ForumUser):
    userdata = user
    userdata.people_reached = Question.objects.filter(
        Q(author=user) | Q(answer__author=user)
    ).aggregate(reach=Coalesce(Sum("views"), 0))["reach"]
    userdata.posts_edited = (
        Question.objects.filter(editor=user).count()
        + Answer.objects.filter(editor=user).count()
    )
    userdata.votes = VoteActivity.objects.filter(
        source=user, reputation_change__isnull=False
    ).count()
    userdata.save()


@job
def calculate_all_users_impact():
    user_qs = ForumUser.objects.filter(is_superuser=False)
    for user in user_qs:
        calculate_user_impact(user)
