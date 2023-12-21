from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import AbstractUser
from django.shortcuts import render, redirect

from forum import models
from forum.apps import logger
from forum.models import Question
from forum.views import utils
from forum.views.helpers import get_questions_queryset
from userauth.models import ForumUser


class QuestionError(Exception):
    pass


def validate_question_data(title: str, content: str) -> None:
    if title is None or len(title) < settings.MIN_QUESTION_TITLE_LENGTH:
        raise QuestionError("Title too short")
    if content is None or len(content) < settings.MIN_QUESTION_CONTENT_LENGTH:
        raise QuestionError(
            f"Content should have at least {settings.MIN_QUESTION_CONTENT_LENGTH} characters"
        )
    if len(title) > settings.MAX_QUESTION_TITLE_LENGTH:
        raise QuestionError("Title too long")
    if len(content) > settings.MAX_QUESTION_CONTENT_LENGTH:
        raise QuestionError("Content too long")


def create_invites(inviter: AbstractUser, question: models.Question, invites: str):
    usernames = invites.split(",") if invites is not None else ""
    users = []
    for username in usernames:
        user = ForumUser.objects.filter(username=username).first()
        if user is None:
            logger.warning(
                f"Failed to invite user {username} to answer question id {question.id} "
                f"because user does not exist"
            )
        else:
            users.append(user)
    utils.create_invites_and_notify_invite_users_to_question(inviter, users, question)


@login_required
def view_similar_questions(request):
    main_query = Question.objects
    q = utils.get_request_param(request, "q", None)
    if not q or len(q) < 4:
        q = utils.get_request_param(request, "title", None)
    if not q or len(q) < 4:
        return render(
            request,
            "main/askquestion.similar-questions.template.html",
            {
                "similar_questions": [],
            },
        )
    all_questions_qs = get_questions_queryset(main_query, None, q, None)
    all_questions_qs = all_questions_qs[:5]
    return render(
        request,
        "main/askquestion.similar-questions.template.html",
        {
            "similar_questions": all_questions_qs,
        },
    )


@login_required
def view_askquestion(request):
    user = request.user
    # New question
    if request.method == "POST":
        questiontaken = request.POST.dict()
        with_answer = questiontaken.get("with_answer", "off") == "on"
        title = questiontaken.get("title")
        content = questiontaken.get("queseditor")
        answer_content = questiontaken.get("answereditor", None)
        tags = questiontaken.get("tags") or ""
        anonymous = questiontaken.get("anonymous", "off") == "on" and not with_answer
        invites = None if with_answer else questiontaken.get("invites")
        try:
            validate_question_data(title, content)
        except QuestionError as e:
            messages.warning(request, f"Error: {e}")
            return render(
                request,
                "main/askquestion.html",
                {
                    "title": title,
                    "content": content,
                    "tags": tags,
                    "allow_anonymous_question": settings.ALLOW_ANONYMOUS_QUESTION,
                },
            )
        question = utils.create_question(
            user,
            title,
            content,
            tags,
            is_anonymous=anonymous,
            send_notifications=not with_answer,
        )
        create_invites(user, question, invites)
        if with_answer and answer_content:
            a = utils.create_answer(
                answer_content, user, question, send_notifications=False
            )
            utils.accept_answer(a)
        messages.success(request, "Question posted successfully")
        return redirect("forum:thread", pk=question.pk)
    return render(
        request,
        "main/askquestion.html",
        {
            "allow_anonymous_question": settings.ALLOW_ANONYMOUS_QUESTION,
        },
    )


def view_markdown_help(request):
    return render(request, "markdown-help.html")
