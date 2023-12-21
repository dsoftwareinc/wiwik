from django.urls import path

from . import views

urlpatterns = [
    path("", views.view_home, name="list"),
    path("query/", views.view_query, name="list_query"),
    path("<str:tag_word>/edit", views.view_edit_tag, name="edit"),
    path("<str:tag_word>/info", views.view_tag_info, name="info"),
    path(
        "tags-autocomplete/",
        views.view_tags_autocomplete,
        name="autocomplete",
    ),
    path("synonyms/", views.view_synonym_list, name="synonyms_list"),
    path(
        "synonyms/approve/<int:synonym_pk>",
        views.view_approve_synonym,
        name="synonyms_approve",
    ),
]
