from django.urls import path

from . import views

urlpatterns = [
    path("flag_model/<int:model_pk>/", views.view_flag_model, name="flag_create"),
    path(
        "edit_model/<str:model_name>/<int:model_pk>/",
        views.view_update_edit_resource,
        name="update_edit_ping",
    ),
]

from wiwik_lib.utils import set_current_site # noqa: E402

set_current_site()
