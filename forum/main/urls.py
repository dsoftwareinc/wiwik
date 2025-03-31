"""forum URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("", include(("forum.urls", "forum"), namespace="forum")),
    path("articles/", include(("articles.urls", "articles"), namespace="articles")),
    path("BB-aDmin/", admin.site.urls),  # intentionally non-standard to prevent casual hacking tries.
    path("scheduler/", include("scheduler.urls")),
    path("accounts/", include("allauth.urls")),
    path("users/", include(("userauth.urls", "userauth"), namespace="userauth")),
    path("badges/", include(("badges.urls", "badges"), namespace="badges")),
    path("tags/", include(("tags.urls", "tags"), namespace="tags")),
    path("general/", include(("wiwik_lib.urls", "wiwik_lib"), namespace="general")),
    path("spaces/", include(("spaces.urls", "spaces"), namespace="spaces")),
    path(
        "similarity/",
        include(("similarity.urls", "similarity"), namespace="similarity"),
    ),
]

if settings.DEBUG_TOOLS:
    urlpatterns.append(path("__debug__/", include("debug_toolbar.urls")))
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
