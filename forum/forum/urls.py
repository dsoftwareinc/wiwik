from django.urls import path

from . import views
from .views.feed import LatestEntriesFeed

urlpatterns = [
    path("", views.view_home, name="home"),
    path("questions/", views.view_questions, name="list"),
    path("questions/tag/<str:tag_word>/", views.view_tag_questions_list, name="tag"),
    path("questions/<int:pk>/", views.view_single_question, name="thread"),
    path("questions/ask", views.view_askquestion, name="ask"),
    path("question/<int:pk>/edit", views.view_editquestion, name="question_edit"),
    path(
        "questions/answer/<int:answer_pk>/edit",
        views.view_editanswer,
        name="answer_edit",
    ),
    path("question/<int:pk>/delete", views.view_delete_question, name="question_delete"),
    path(
        "question/<int:question_pk>/delete/<int:answer_pk>",
        views.view_delete_answer,
        name="answer_delete",
    ),
]
# Partials
urlpatterns += [
    path(
        "questions/<int:question_pk>/tags",
        views.view_partial_question_tags,
        name="question_tags",
    ),
    path(
        "<str:post_type>/<int:post_pk>/comments",
        views.view_partial_post_comments,
        name="post_comments",
    ),
    path(
        "questions/<int:question_pk>/invites",
        views.view_partial_invites,
        name="questions_invites",
    ),
    path("users/navbar", views.view_partial_user_navbar, name="user_navbar"),
    path("similar-questions/", views.view_similar_questions, name="similar"),
    path("tags/<int:pk>/popover", views.view_partial_tag_popover, name="tag_popover"),
]
# Actions
urlpatterns += [
    path("question/<int:pk>/follow/", views.view_follow_question, name="follow"),
    path("question/<int:pk>/unfollow/", views.view_unfollow_question, name="unfollow"),
    path(
        "question/<int:question_pk>/bookmark",
        views.view_bookmark_question,
        name="bookmark",
    ),
    path(
        "question/<int:question_pk>/unbookmark",
        views.view_unbookmark_question,
        name="unbookmark",
    ),
    path("usertags/<str:tag_word>/watch", views.view_user_follow_tag, name="watch_tag"),
    path(
        "usertags/<str:tag_word>/unwatch",
        views.view_user_unfollow_tag,
        name="unwatch_tag",
    ),
    path(
        "question/<int:question_pk>/invite_to_question",
        views.view_invite_to_question,
        name="invite",
    ),
    path(
        "question/<int:question_pk>/download_markdown",
        views.view_download_thread,
        name="markdown",
    ),
    path(
        "question/<int:pk>/upvote_comment/<str:parent_model_name>/<int:comment_pk>",
        views.view_upvote_comment,
        name="comment_upvote",
    ),
    path(
        "question/<int:pk>/delete_comment/<str:model>/<int:comment_id>",
        views.view_deletecomment,
        name="comment_delete",
    ),
]
# Automatic actions
urlpatterns += [
    path(
        "question/<int:pk>/upvote/<str:model_name>/<int:model_pk>",
        views.view_upvote,
        name="upvote",
    ),
    path(
        "question/<int:pk>/downvote/<str:model_name>/<int:model_pk>",
        views.view_downvote,
        name="downvote",
    ),
    path(
        "mark_as_seen/<int:vote_activity_pk>/",
        views.view_mark_as_seen,
        name="mark_seen",
    ),
    path("mark_all_as_seen/", views.view_all_mark_as_seen, name="mark_all_seen"),
    path(
        "question/<int:question_pk>/accept/<int:answer_pk>",
        views.view_acceptanswer,
        name="answer_accept",
    ),
]

urlpatterns += [
    path("users-autocomplete/", views.view_users_autocomplete, name="users_autocomplete"),
    path("users-get/", views.view_get_users_data, name="users-get"),
    path("image-upload/", views.view_image_upload, name="image_upload"),
]
# Slack
urlpatterns += [
    path("integrations/slack_post/", views.view_slack_post, name="slack-post"),
    path(
        "integrations/tags_autocomplete/",
        views.view_tags_autocomplete_for_slack,
        name="slack-tags-autocomplete",
    ),
    path("integrations/slack_search/", views.search_from_slack, name="slack-search"),
]

# RSS
urlpatterns += [
    path("rss/feed/", LatestEntriesFeed()),
    path("editing-help/", views.view_markdown_help),
]

# One time code
from wiwik_lib.templatetags.wiwik_template_tags import check_latex_config  # noqa: E402
from forum.integrations.slack_api import configure_slack_client  # noqa: E402

check_latex_config()
configure_slack_client()
