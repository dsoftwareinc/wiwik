from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from forum import models, jobs
from forum.apps import logger
from forum.views import utils


@login_required
def view_acceptanswer(request, question_pk: int, answer_pk: int):
    user = request.user
    try:
        question = models.Question.objects.get(pk=question_pk)
        answer = models.Answer.objects.get(pk=answer_pk)
    except models.Question.DoesNotExist:
        logger.warning(f"Question {question_pk} does not exists")
        return redirect('forum:list')
    except models.Answer.DoesNotExist:
        logger.warning(f"Answer {answer_pk} does not exists")
        return redirect('forum:thread', pk=question_pk)
    if answer.question != question:
        logger.warning(f"Trying to approve answer {answer_pk} for question"
                       f" {question_pk} but answer is for a different question")
        return redirect('forum:thread', pk=question_pk)
    if question.author != user and not user.is_staff:
        logger.warning(f"user {user.username} trying to approve answer on question"
                       f" {question_pk} without permission")
        return redirect('forum:thread', pk=question_pk)
    utils.accept_answer(answer)
    answers = answer.question.answer_set.all()
    for answer in answers:
        utils.delete_activity(answer.question.author, answer.author, answer, settings.ACCEPT_ANSWER_CHANGE)
    if user != answer.author:
        if question.is_old and answer.is_recent:
            change = settings.ACCEPT_ANSWER_OLD_QUESTION_CHANGE
        else:
            change = settings.ACCEPT_ANSWER_CHANGE
        utils.create_activity(user, answer.author, answer, change)
        jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES['Accept answer'])
    logger.info(f"user {user.username} approved answer {answer_pk} "
                f"on question {question_pk}")
    messages.success(request, "Answer accepted")
    return redirect('forum:thread', pk=question_pk)
