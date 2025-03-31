from scheduler import job

from forum.models import Question
from forum.views.follow_models import handle_user_tag_stats
from forum.views.utils import recalculate_user_reputation
from userauth.models import ForumUser


@job()
def update_user_tag_stats(post_id: int, user_id: int):
    post = Question.objects.get(id=post_id)
    user = ForumUser.objects.get(id=user_id)
    tags_to_update = post.tags.all()
    for tag in tags_to_update:
        # Actual calculation
        handle_user_tag_stats(tag, user)


@job()
def recalculate_user_reputation_score():
    posts = Question.objects.all()
    users = ForumUser.objects.all()
    for user in users:
        recalculate_user_reputation(user)
        for post in posts:
            update_user_tag_stats(post.id, user.id)
