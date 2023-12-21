from django.urls import path, re_path

from . import views
from .admin import SendUserEmails

urlpatterns = [
    path("signup/", views.view_signup, name="signup"),
    path("login/", views.view_login, name="login"),
    path("logout/", views.view_logout, name="logout"),
    path(
        "staff-deactivate/<str:username>/",
        views.view_deactivate_user,
        name="deactivate_user",
    ),
    path(
        "staff-activate/<str:username>/", views.view_activate_user, name="activate_user"
    ),
    path("editprofile/", views.view_editprofile, name="edit"),
    path("editprofile/profile-pic/", views.view_profile_pic, name="profile_pic"),
    path("profile/<str:username>/<str:tab>/", views.view_profile, name="profile"),
    re_path(
        r"^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]+)/$",
        views.view_activate,
        name="activate",
    ),
    path("", views.view_users, name="list"),
    path("query/", views.view_users_query, name="list_query"),
    re_path(
        r"^unsubscribe/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]+)/$",
        views.view_unsubscribe,
        name="unsubscribe",
    ),
    path("email-users/", SendUserEmails.as_view(), name="admin_email"),
]
