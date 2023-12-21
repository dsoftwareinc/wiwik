from datetime import timedelta
from typing import cast, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists, OuterRef, Value
from django.shortcuts import render, redirect
from django.utils import timezone
from scheduler import job

from common import utils as common_utils
from forum import jobs
from forum.apps import logger
from forum.models import Question, VoteActivity, QuestionView, QuestionBookmark, Answer, Comment
from forum.views import utils
from userauth.models import ForumUser
from wiwik_lib.models import user_model_defer_fields


def _get_question_answers(q: Question, order_by: str, user):
    """Get all questions answers ordered_by."""
    match order_by:
        case 'oldest':
            order_by_field = 'created_at'
        case 'latest':
            order_by_field = '-created_at'
        case _:
            order_by_field = '-votes'
    qs = (
        q.answer_set.all()
        # .annotate(num_comments=Subquery(c_subquery))
        .select_related('author', 'editor', )
        .defer(*user_model_defer_fields('author'), *user_model_defer_fields('editor'))
        .prefetch_related('comments', 'comments__author')
        .annotate(
            user_upvoted=Exists(VoteActivity.objects.filter(
                answer_id=OuterRef('id'), source=user, reputation_change=settings.UPVOTE_CHANGE)))
        .annotate(
            user_downvoted=Exists(VoteActivity.objects.filter(
                question_id=OuterRef('id'), source=user, reputation_change=settings.DOWNVOTE_CHANGE)))
        .order_by(order_by_field)
    )

    return list(qs)


def _create_answer_and_message(request, question_pk: int, answer_content: str) -> None:
    question = Question.objects.filter(pk=question_pk).first()
    if question is None:
        logger.warning('Trying to create answer without question, ignoring')
        return
    if question.answer_set.count() >= settings.MAX_ANSWERS:
        logger.warning(f'User {request.user} tries to create answer for question {question_pk} '
                       f'when it already reached max number of answers')
        return
    a = utils.create_answer(answer_content, request.user, question)
    if a is not None:
        messages.success(request, 'Answer posted successfully')


def _create_comment(request, model_name: str, model_pk: int, content: str) -> Optional[Comment]:
    parent = utils.get_model(model_name, model_pk)
    if not (settings.MIN_COMMENT_LENGTH <= len(content) <= settings.MAX_COMMENT_LENGTH):
        logger.warning(f'user {request.user} trying to create a comment '
                       f'on {model_name}:{model_pk} with bad length ({len(content)})')
        messages.error(request, f'Can not create comment with length {len(content)}', 'danger')
        return None
    if parent is None:
        logger.warning(f'Trying to comment on {model_name}:{model_pk} which could not be fetched')
        return None
    if parent.comments.count() >= settings.MAX_COMMENTS:
        logger.warning(f'User {request.user} tries to create comment for {model_name}:{model_pk} '
                       f'when it already reached max number of comments')
        return None
    return utils.create_comment(content, request.user, parent)


def _do_single_question_post_action(request, question_pk: int):
    """Create new answer or new comment in a question thread.

    :param request:
    :param question_pk: Question pk, for redirecting back to the main thread view.
    :return:
    """
    params = request.POST.dict()
    action = params.get('action')
    if action == 'create_answer':  # Handle adding answer
        _create_answer_and_message(request, question_pk, params.get('editor1'))
    elif action == 'create_comment':  # Handle adding comment
        _create_comment(request, params.get('model'), params.get('model_pk'), params.get('comment'))
    else:
        logger.warning(f'{request.user} tried to perform an unknown action "{action}"')
    return redirect('forum:thread', pk=question_pk)


@job
def view_thread_background_tasks(user: ForumUser, q: Question):
    if q.author == user:
        return
    last_hour = timezone.now() - timedelta(hours=1)
    if not q.viewed_by(user, last_hour):
        QuestionView.objects.create(author=user, question=q, )
    unseen_activities = (VoteActivity.objects
                         .filter(target=user, question=q, seen=None)
                         )
    unseen_count = unseen_activities.count()
    logger.debug(f'Marking {unseen_count} activities as seen')
    unseen_activities.update(seen=timezone.now())


@login_required
def view_single_question(request, pk):
    # Handle adding new answer/comment
    if request.method == 'POST':
        return _do_single_question_post_action(request, pk)
    try:
        q = Question.objects.get(pk=pk)
        user_upvoted = Exists(VoteActivity.objects.filter(
            question_id=pk, answer_id__isnull=True, source=request.user, reputation_change=settings.UPVOTE_CHANGE))
        user_downvoted = Exists(VoteActivity.objects.filter(
            question_id=pk, source=request.user, reputation_change=settings.DOWNVOTE_CHANGE))
        q = (Question.objects
             .annotate(user_follows=Value(q.follows.filter(user=request.user).exists()))
             .annotate(user_bookmarked=Exists(QuestionBookmark.objects.filter(user=request.user, question_id=pk)))
             .annotate(user_answered=Exists(Answer.objects.filter(author=request.user, question_id=pk)))
             .annotate(user_upvoted=user_upvoted)
             .annotate(user_downvoted=user_downvoted)
             .select_related('author', 'editor', )
             .defer(*user_model_defer_fields('author'), *user_model_defer_fields('editor'))
             .get(pk=pk))
    except Question.DoesNotExist:
        return redirect('forum:list')
    attrs = (Question.objects.only('id')
             .annotate(num_bookmarks=Count('bookmarks'))
             .get(pk=pk))
    q.num_bookmarks = attrs.num_bookmarks

    user: ForumUser = cast(ForumUser, request.user)
    show_follow = not q.user_follows
    show_accept_button = (q.author == user or user.can_edit or user.is_staff)
    show_edit_button = (q.author == user or user.can_edit)
    show_delete_q_button = (q.author == user or user.can_delete_question)
    show_delete_a_button = user.can_delete_answer
    order_answers_by = common_utils.get_request_param(request, 'order_by', 'votes')
    all_answers = _get_question_answers(q, order_answers_by, request.user)
    bookmarked = q.user_bookmarked

    jobs.start_job(view_thread_background_tasks, request.user, q)

    return render(request, 'main/thread.template.html',
                  {'q': q,
                   'num_bookmarks': q.num_bookmarks,
                   'all_answers': all_answers,
                   'show_accept_button': show_accept_button,
                   'show_edit_button': show_edit_button,
                   'show_delete_q_button': show_delete_q_button,
                   'show_delete_a_button': show_delete_a_button,
                   'max_answers': settings.MAX_ANSWERS,
                   'show_follow': show_follow,
                   'bookmarked': bookmarked,
                   'order_by': order_answers_by,
                   'title': q.title,
                   })
