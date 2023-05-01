from django.urls import path

from . import views

urlpatterns = [
    path('', views.view_landing_page, name='landing-page'),
]
