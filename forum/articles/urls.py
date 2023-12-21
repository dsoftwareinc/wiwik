from django.urls import path

from . import views

# Articles
urlpatterns = [
    path("", views.view_article_list, name="list"),
    path("<int:pk>/", views.view_article_detail, name="detail"),
    path("create/", views.view_article_create, name="create"),
    path("<int:pk>/edit/", views.view_article_edit, name="edit"),
    path("<int:pk>/delete/", views.view_article_delete, name="delete"),
]
