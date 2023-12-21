from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from forum import models, jobs
from forum.apps import logger


@login_required
def view_bookmark_question(request, question_pk: int):
    if request.method != "GET":
        logger.warning(f"user {request.user.username} is trying to make a request not through the app")
        return redirect("forum:thread", pk=question_pk)
    question = models.Question.objects.filter(pk=question_pk).first()
    if question is None:
        logger.warning(f"User {request.user.username} is trying to delete bookmark on a non existing question")
        return redirect("forum:thread", pk=question_pk)
    user = request.user
    existing = models.QuestionBookmark.objects.filter(user=user, question=question).first()
    if existing is not None:
        logger.debug(f"User {user.username} already bookmarked question id {question.id}")
        messages.info(request, "Bookmark already exists")
        return redirect("forum:thread", pk=question_pk)
    logger.debug(f"Creating bookmark for [user={user.username} question={question.id}]")
    models.QuestionBookmark.objects.create(user=user, question=question)
    jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Bookmark thread"])
    return redirect("forum:thread", pk=question_pk)


@login_required
def view_unbookmark_question(request, question_pk: int):
    if request.method != "GET":
        logger.warning(f"user {request.user.username} is trying to make a request not through the app")
        return redirect("forum:thread", pk=question_pk)
    question = models.Question.objects.filter(pk=question_pk).first()
    if question is None:
        logger.warning(f"User {request.user.username} is trying to delete bookmark on a non existing question")
        return redirect("forum:thread", pk=question_pk)
    user = request.user
    existing = models.QuestionBookmark.objects.filter(user=user, question=question).first()
    if existing is None:
        logger.debug(
            f"User {user.username} tries to delete bookmark for question "
            f"id {question.id} but bookmark does not exist"
        )
        messages.info(request, "Bookmark for question does not exist")
        return redirect("forum:thread", pk=question_pk)
    existing.delete()
    return redirect("forum:thread", pk=question_pk)
