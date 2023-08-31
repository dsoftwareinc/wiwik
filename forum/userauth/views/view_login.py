from allauth.socialaccount.models import SocialApp
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import render, redirect
from django.urls import reverse, resolve, Resolver404

from userauth.apps import logger


def view_login(request):
    if request.method == "POST":
        next_url = request.GET['next'] if 'next' in request.GET else reverse('forum:home')
        try:
            resolve(next_url)
        except Exception:
            logger.warning(f'Bad redirect url: {next_url}')
            next_url = reverse('forum:home')
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are logged in as <b>{user.display_name()}</b>")
                url = next_url
                try:
                    resolve(next_url)
                except Resolver404:
                    url = reverse('forum:home')
                return redirect(url)
            else:
                messages.error(request, "Invalid username or password", 'danger')
        else:
            messages.error(request, "Invalid username or password", 'danger')
    if isinstance(request.user, AnonymousUser):
        form = AuthenticationForm()
        google_login_allowed = (SocialApp.objects.filter(provider='google').count() > 0)
        facebook_login_allowed = (SocialApp.objects.filter(provider='facebook').count() > 0)
        okta_login_allowed = (SocialApp.objects.filter(provider='okta').count() > 0)
        return render(request, "userauth/login.html", {
            "form": form,
            "google_login_allowed": google_login_allowed,
            "facebook_login_allowed": facebook_login_allowed,
            "okta_login_allowed": okta_login_allowed,
        })
    else:
        messages.info(request, 'User already logged in')
        return redirect('forum:list')
