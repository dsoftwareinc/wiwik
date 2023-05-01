import os
import random

from django.conf import settings

from wiwik_lib.utils import ManagementCommand
from forum.apps import logger
from forum.models import Question
from forum.views import utils
from userauth.models import ForumUser


def is_job(func):
    return hasattr(func, 'delay')


def random_user_generator():
    users = ForumUser.objects.all()
    while True:
        yield random.choice(users)


random_user = random_user_generator()


def change_author(question: Question):
    question.author = next(random_user)


def edit_question(question: Question):
    logger.info(f'Editing question {question.id}')
    utils.update_question(
        next(random_user), question,
        question.title + ' ', question.content,
        ','.join(question.tag_words())
    )


def upvote_question(question):
    max_votes = 20
    num_upvotes = random.randint(0, max_votes)
    logger.info(f'Upvoting question:{question.id} {num_upvotes} times')
    for _ in range(num_upvotes):
        utils.upvote(next(random_user), question)
    answers = question.answer_set.all()
    for answer in answers:
        num_upvotes = random.randint(0, int(max_votes / 2))
        logger.info(f'Upvoting answer:{answer.id} {num_upvotes} times')
        for _ in range(num_upvotes):
            utils.upvote(next(random_user), answer)


class Command(ManagementCommand):
    help = 'Change authors, etc.'

    def handle(self, *args, **options):
        question_list = Question.objects.all()
        for question in question_list:
            change_author(question)
            if random.random() < 0.2:
                edit_question(question)
            upvote_question(question)
            question.views = random.randint(1, 5000)
            question.save()

        filenames = os.listdir(os.path.join(settings.MEDIA_ROOT, 'default_pics'))
        user_list = ForumUser.objects.all()
        for user in user_list:
            profile_pic_filename = 'default_pics/' + random.choice(filenames)
            user.profile_pic = profile_pic_filename
            logger.info(f'Resetting profile-pic for {user.username}: using {profile_pic_filename}')
            user.save()
