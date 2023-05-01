from abc import ABC

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.shortcuts import render


class ManagementCommand(BaseCommand, ABC):

    def print(self, *args):
        self.stdout.write(self.style.SUCCESS(*args))

    def error_print(self, *args):
        self.stdout.write(self.style.ERROR(*args))


def under_construction_response(request):
    return render(request, 'under-construction.html')


def is_email_allowed(email_address: str) -> bool:
    """Is email address valid in the site settings"""
    if not settings.ALLOWED_REGISTRATION_EMAIL_DOMAINS:
        return True
    user_email_domain = email_address.split('@')[1]
    return user_email_domain in settings.ALLOWED_REGISTRATION_EMAIL_DOMAINS


def paginate_queryset(qs: QuerySet, page: int, per_page: int):
    # Pagination
    paginator = Paginator(qs, per_page)
    return paginator.get_page(page)


try:
    CURRENT_SITE = str(Site.objects.get_current())
    if not CURRENT_SITE.startswith('http'):
        CURRENT_SITE = 'http://' + CURRENT_SITE
except Exception:
    CURRENT_SITE = 'http://localhost:8000'
