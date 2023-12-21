from django.urls import path

from . import views

urlpatterns = [
    path("user-spaces", views.view_side_menu_user_spaces, name="user-spaces"),
    path("<str:space_id>/info", views.view_space_info, name="detail"),
    path("<int:space_id>/edit", views.view_space_edit, name="edit"),
    path("<str:space_id>/leave", views.view_space_leave, name="leave"),
    path("<str:space_id>/join", views.view_space_join, name="join"),
    path("<str:space_id>/questions", views.view_space_questions, name="questions"),
    path(
        "latest-questions",
        views.view_user_spaces_latest_questions,
        name="user-spaces-questions",
    ),
    path("property/<str:property_name>", views.view_property_info, name="property-info"),
]
