import re

from django.core.mail import mail_admins
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from landingpage.apps import logger
from landingpage.models import Lead


def valid_email(email):
    return bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", email))


def view_landing_page(request):
    if request.method == 'POST':
        data = request.POST.dict()
        email = data.get('email', None)
        if not valid_email(email):
            logger.warn(f"Invalid email {email}")
            return HttpResponseBadRequest()
        msg = data.get('message', None)
        Lead.objects.create(email=email, message=msg)
        logger.info(f"Got lead with email {email} msg {msg}")
        mail_admins("New lead", f"Got lead with email {email} msg {msg}")
        return render(request, 'thank-you.html')
    return render(request, 'landing.html')
