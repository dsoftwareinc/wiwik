from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Exists
from django.shortcuts import get_object_or_404, redirect, render

from articles.apps import logger
from articles.models import Article
from common import utils as common_utils
from forum import jobs
from forum.models import QuestionFollow, QuestionBookmark, VoteActivity
from forum.views import utils
from forum.views.helpers import _get_questions_queryset
from forum.views.q_and_a_crud.view_ask_question import QuestionError
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from main import settings
from wiwik_lib.models import user_model_defer_fields
from wiwik_lib.utils import paginate_queryset
from wiwik_lib.views import ask_to_edit_resource, finish_edit_resource


@login_required
def view_article_list(request):
    tag_user_follows = utils.get_user_followed_tags(request.user)
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    q = utils.get_request_param(request, 'q', None)
    header = 'All articles' if q is None else 'Search results'
    base_qs = Article.objects.filter(type__in=Article.POST_ARTICLE_TYPES)
    tab = common_utils.get_request_tab(request)
    q = utils.get_request_param(request, 'q', None)
    all_questions_qs = _get_questions_queryset(
        base_qs.filter(space__isnull=True), tab, q, request.user)
    all_questions_qs = all_questions_qs.prefetch_related('tags', )
    page_number = request.GET.get('page', 1)
    page_qs = paginate_queryset(all_questions_qs, page_number, settings.QUESTIONS_PER_PAGE)
    context = {
        'all_questions': page_qs,
        'tab': tab if q is None else None,
        'header': header,
        'tags_watched': tag_words_user_follows,
        'query': q,
    }
    return render(request, 'articles/articles-list.html', context)


def _do_article_create_post_action(request, pk):
    # TODO
    pass


def validate_article_data(title: str, content: str) -> None:
    if title is None or len(title) < settings.MIN_ARTICLE_TITLE_LENGTH:
        raise QuestionError("Title too short")
    if content is None or len(content) < settings.MIN_QUESTION_CONTENT_LENGTH:
        raise QuestionError(f"Content should have at least {settings.MIN_QUESTION_CONTENT_LENGTH} characters")
    if len(title) > settings.MAX_QUESTION_TITLE_LENGTH:
        raise QuestionError("Title too long")


@login_required
def view_article_detail(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect('forum:thread', pk=pk)
    # Handle adding new comment
    if request.method == 'POST':
        return _do_article_create_post_action(request, pk)
    user_upvoted = Exists(VoteActivity.objects.filter(
        question_id=pk, answer_id__isnull=True, source=request.user, reputation_change=settings.UPVOTE_CHANGE))
    user_downvoted = Exists(VoteActivity.objects.filter(
        question_id=pk, source=request.user, reputation_change=settings.DOWNVOTE_CHANGE))
    article = (Article.objects
               .annotate(user_follows=Exists(QuestionFollow.objects.filter(question_id=pk, user=request.user)))
               .annotate(user_bookmarked=Exists(QuestionBookmark.objects.filter(user=request.user, question_id=pk)))
               .annotate(user_upvoted=user_upvoted)
               .annotate(user_downvoted=user_downvoted)
               .select_related('author', )
               .defer(*user_model_defer_fields('author'), )
               .get(pk=pk))

    attrs = (Article.objects.only('id')
             .annotate(num_bookmarks=Count('bookmarks'))
             .get(pk=pk))
    article.num_bookmarks = attrs.num_bookmarks

    user = request.user
    show_follow = not article.user_follows
    show_edit_button = (article.author == user or user.has_perm('article_edit'))
    show_delete_q_button = (article.author == user or user.has_perm('article_delete'))
    order_answers_by = utils.get_request_param(request, 'order_by', 'votes')
    bookmarked = article.user_bookmarked

    jobs.start_job(view_thread_background_tasks, request.user, article)

    return render(request, 'articles/articles-detail.html',
                  {'q': article,
                   'num_bookmarks': article.num_bookmarks,
                   'show_edit_button': show_edit_button,
                   'show_delete_q_button': show_delete_q_button,
                   'show_follow': show_follow,
                   'bookmarked': bookmarked,
                   'order_by': order_answers_by,
                   'title': article.title,
                   })


@login_required
def view_article_delete(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect('forum:thread', pk=pk)
    user = request.user

    if not article.user_can_delete(user):
        logger.warning(f'user {user.username} tried to delete article {pk} '
                       f'which does they do not have permission to delete')
        return redirect('articles:details', pk=pk)
    if request.method == 'POST':
        utils.delete_question(article)
        messages.success(request, "Article deleted")
        return redirect('articles:list')
    # Get request
    return render(request, 'articles/articles-delete.html', {
        'title': article.title,
        'content': article.content,
        'pk': pk,
    })


@login_required
def view_article_edit(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect('forum:thread', pk=pk)
    user = request.user
    if article.author != user and not user.can_edit:  # TODO change edit user permissions
        messages.error(request, 'You can not edit this article', 'danger')
        return redirect('article:detail', pk=pk)
    if not ask_to_edit_resource(request.user, article):
        messages.warning(request, 'Article is currently edited by a different user')
        return redirect('article:detail', pk=pk)
    title = article.title
    content = article.content
    tags = ','.join(article.tag_words())
    # Update article
    if request.method == 'POST':
        questiontaken = request.POST.dict()
        title = questiontaken.get('title')
        content = questiontaken.get('articleeditor')
        tags = questiontaken.get('tags') or ''
        try:
            validate_article_data(title, content)
            finish_edit_resource(article)
            utils.update_question(user, article, title, content, tags)
            messages.success(request, 'Article updated successfully')
            return redirect('articles:detail', pk=pk)
        except QuestionError as e:
            messages.warning(request, f'Error: {e}')
    # Request to edit
    return render(request, 'articles/articles-edit.html', {
        'title': title,
        'content': content,
        'tags': tags,
        'article_pk': pk,
    })


@login_required
def view_article_create(request):
    user = request.user
    # New article
    if request.method == 'POST':
        data = request.POST.dict()
        title = data.get('title')
        content = data.get('articleeditor')
        tags = data.get('tags') or ''
        try:
            validate_article_data(title, content)
        except QuestionError as e:
            messages.warning(request, f'Error: {e}')
            return render(request, 'articles/articles-create.html', {
                'title': title,
                'content': content,
                'tags': tags,
            })
        article = utils.create_question(user, title, content, tags, type='a')
        messages.success(request, 'Article draft posted successfully')
        return redirect('articles:detail', pk=article.pk)
    return render(request, 'articles/articles-create.html', {

    })
