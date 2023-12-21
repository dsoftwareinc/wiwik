from typing import cast

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, Value
from django.shortcuts import get_object_or_404, redirect, render

from articles.apps import logger
from articles.models import Article
from common import utils as common_utils
from forum import jobs
from forum.models import QuestionBookmark, VoteActivity
from forum.views import utils
from forum.views.helpers import get_questions_queryset
from forum.views.q_and_a_crud.view_thread import view_thread_background_tasks
from forum.views.utils import get_view_name_for_post_type, user_has_perm
from userauth.models import ForumUser
from wiwik_lib.models import user_model_defer_fields
from wiwik_lib.utils import paginate_queryset
from wiwik_lib.views import ask_to_edit_resource, finish_edit_resource


@login_required
def view_article_list(request):
    tag_user_follows = utils.get_user_followed_tags(request.user)
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    q = utils.get_request_param(request, "q", None)
    header = "All articles" if q is None else "Search results"
    base_qs = Article.objects.filter(type__in=Article.POST_ARTICLE_TYPES)
    tab = common_utils.get_request_tab(request)
    q = utils.get_request_param(request, "q", None)
    all_questions_qs = get_questions_queryset(base_qs.filter(space__isnull=True), tab, q, request.user)
    all_questions_qs = all_questions_qs.prefetch_related(
        "tags",
    )
    page_number = request.GET.get("page", 1)
    page_qs = paginate_queryset(all_questions_qs, page_number, settings.QUESTIONS_PER_PAGE)
    context = {
        "all_questions": page_qs,
        "tab": tab if q is None else None,
        "header": header,
        "tags_watched": tag_words_user_follows,
        "query": q,
    }
    return render(request, "articles/articles-list.html", context)


def _create_comment(request, model_name: str, model_pk: int, content: str):
    parent = utils.get_model(model_name, model_pk)
    if not (settings.MIN_COMMENT_LENGTH <= len(content) <= settings.MAX_COMMENT_LENGTH):
        logger.warning(
            f"user {request.user} trying to create a comment "
            f"on {model_name}:{model_pk} with bad length ({len(content)})"
        )
        messages.error(request, f"Can not create comment with length {len(content)}", "danger")
        return None
    if parent is None:
        logger.warning(f"Trying to comment on {model_name}:{model_pk} which could not be fetched")
        return None
    if parent.comments.count() >= settings.MAX_COMMENTS:
        logger.warning(
            f"User {request.user} tries to create comment for {model_name}:{model_pk} "
            f"when it already reached max number of comments"
        )
        return None
    utils.create_comment(content, request.user, parent)


def _do_article_create_post_action(request, pk):
    """Article details POST actions.

    Create new comment in an article.

    :param request:
    :param pk: Article pk, for redirecting back to the main thread view.
    :return:
    """
    params = request.POST.dict()
    action = params.get("action")
    if action == "create_comment":  # Handle adding comment
        _create_comment(request, params.get("model"), params.get("model_pk"), params.get("comment"))
    else:
        logger.warning(f'{request.user} tried to perform an unknown action "{action}" on article:{pk}')
    return redirect("articles:detail", pk=pk)


class ArticleValidationError(Exception):
    pass


def _validate_article_data(title: str, content: str) -> None:
    if title is None or len(title) < settings.MIN_ARTICLE_TITLE_LENGTH or len(title) > 255:
        length = len(title) if title is not None else 0
        raise ArticleValidationError(
            f"Title has {length} characters, must be between {settings.MIN_ARTICLE_TITLE_LENGTH} and 255 characters."
        )
    if (
        content is None
        or len(content) < settings.MIN_ARTICLE_CONTENT_LENGTH
        or len(content) > settings.MAX_ARTICLE_CONTENT_LENGTH
    ):
        length = len(content) if content is not None else 0
        raise ArticleValidationError(
            f"Content length is {length} characters, should be between "
            f"{settings.MIN_ARTICLE_CONTENT_LENGTH} "
            f"and {settings.MAX_ARTICLE_CONTENT_LENGTH} characters"
        )


@login_required
def view_article_detail(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect(get_view_name_for_post_type(article), pk=pk)
    # Handle adding new comment
    if request.method == "POST":
        return _do_article_create_post_action(request, pk)
    user_upvoted = Exists(
        VoteActivity.objects.filter(
            question_id=pk,
            answer_id__isnull=True,
            source=request.user,
            reputation_change=settings.UPVOTE_CHANGE,
        )
    )
    user_downvoted = Exists(
        VoteActivity.objects.filter(
            question_id=pk,
            source=request.user,
            reputation_change=settings.DOWNVOTE_CHANGE,
        )
    )
    article = (
        Article.objects.annotate(user_follows=Value(article.follows.filter(user=request.user).exists()))
        .annotate(user_bookmarked=Exists(QuestionBookmark.objects.filter(user=request.user, question_id=pk)))
        .annotate(user_upvoted=user_upvoted)
        .annotate(user_downvoted=user_downvoted)
        .select_related(
            "author",
        )
        .defer(
            *user_model_defer_fields("author"),
        )
        .get(pk=pk)
    )

    num_bookmarks = article.bookmarks.count()

    user = request.user
    show_follow = not article.user_follows
    show_edit_button = article.author == user or user.has_perm("article_edit")
    show_delete_q_button = article.author == user or user.has_perm("article_delete")
    order_answers_by = utils.get_request_param(request, "order_by", "votes")
    bookmarked = article.user_bookmarked

    jobs.start_job(view_thread_background_tasks, request.user, article)

    return render(
        request,
        "articles/articles-detail.html",
        {
            "q": article,
            "num_bookmarks": num_bookmarks,
            "show_edit_button": show_edit_button,
            "show_delete_q_button": show_delete_q_button,
            "show_follow": show_follow,
            "bookmarked": bookmarked,
            "order_by": order_answers_by,
            "title": article.title,
        },
    )


@login_required
def view_article_delete(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect(get_view_name_for_post_type(article), pk=pk)
    user = request.user
    if not article.user_can_delete(user):
        logger.warning(
            f"user {user.username} tried to delete article {pk} " f"which does they do not have permission to delete"
        )
        return redirect("articles:detail", pk=pk)
    if request.method == "POST":
        utils.delete_question(article)
        messages.success(request, "Article deleted")
        return redirect("articles:list")
    # Get request
    return render(
        request,
        "articles/articles-delete.html",
        {
            "title": article.title,
            "content": article.content,
            "pk": pk,
        },
    )


@login_required
def view_article_edit(request, pk: int):
    article = get_object_or_404(Article, pk=pk)
    if not article.is_article:
        return redirect(get_view_name_for_post_type(article), pk=pk)
    user: ForumUser = cast(ForumUser, request.user)
    if not user_has_perm("edit", user, "article", pk):
        messages.error(request, "You can not edit this article", "danger")
        return redirect("articles:detail", pk=pk)
    if not ask_to_edit_resource(request.user, article):
        messages.warning(request, "Article is currently edited by a different user")
        return redirect("articles:detail", pk=pk)
    title = article.title
    content = article.content
    tags = ",".join(article.tag_words())
    # Update article
    if request.method == "POST":
        post_data = request.POST.dict()
        title = post_data.get("title")
        content = post_data.get("articleeditor")
        tags = post_data.get("tags") or ""
        try:
            _validate_article_data(title, content)
            finish_edit_resource(article)
            utils.update_question(user, article, title, content, tags)
            messages.success(request, "Article updated successfully")
            return redirect("articles:detail", pk=pk)
        except ArticleValidationError as e:
            messages.warning(request, f"Error: {e}")
    # Request to edit
    return render(
        request,
        "articles/articles-edit.html",
        {
            "title": title,
            "content": content,
            "tags": tags,
            "article_pk": pk,
        },
    )


@login_required
def view_article_create(request):
    user = request.user
    # New article
    if request.method == "GET":
        return render(request, "articles/articles-create.html", {})
    if request.method != "POST":
        logger.warning(f"{user.username} tried {request.path} with HTTP {request.method}")
        return render(request, "articles/articles-create.html", {})
    data = request.POST.dict()
    title = data.get("title")
    content = data.get("articleeditor")
    tags = data.get("tags") or ""
    try:
        _validate_article_data(title, content)
    except ArticleValidationError as e:
        messages.warning(request, f"Error: {e}")
        return render(
            request,
            "articles/articles-create.html",
            {
                "title": title,
                "content": content,
                "tags": tags,
            },
        )
    article = utils.create_article(user, title, content, tags)
    messages.success(request, "Article draft posted successfully")
    return redirect("articles:detail", pk=article.pk)
