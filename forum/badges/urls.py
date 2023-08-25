from django.urls import path

from . import views

urlpatterns = [
    path('<int:badge_id>/', views.view_single_badge, name='detail'),
    path('list/', views.view_badges, name='list'),

]
