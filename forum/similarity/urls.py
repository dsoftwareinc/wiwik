from django.urls import path

from . import views

urlpatterns = [
    path(
        "questions/<int:question_pk>/related",
        views.view_partial_related_questions,
        name="related",
    ),
]
