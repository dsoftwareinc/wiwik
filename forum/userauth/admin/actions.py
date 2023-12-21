import markdown
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import FormView
from pymdownx import superfences

from forum.jobs.moderator_check import grant_moderator
from userauth.models import ForumUser, UserVisit
from wiwik_lib.models import Follow

MARKDOWN_EXTENSIONS = [
    "pymdownx.magiclink",
    "pymdownx.extra",
    "pymdownx.superfences",
]
MARKDOWN_EXTENSIONS_CONFIG = {
    "pymdownx.superfences": {
        "custom_fences": [
            {
                "name": "mermaid",
                "class": "mermaid",
                "format": superfences.fence_div_format,
            }
        ]
    },
}


def markdownify(text: str):
    html = markdown.markdown(
        text,
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSIONS_CONFIG,
    )
    return html


class SendEmailForm(forms.Form):
    subject = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Subject"}))
    users = forms.ModelMultipleChoiceField(label="To", queryset=ForumUser.objects.all(), widget=forms.SelectMultiple())
    message = forms.Field()


@admin.action(description="Send email")
def send_email(self, request, queryset):
    form = SendEmailForm(initial={"users": queryset})
    return render(request, "admin/send_email.html", {"form": form})


class SendUserEmails(FormView):
    template_name = "admin/send_email.html"
    form_class = SendEmailForm
    success_url = reverse_lazy("admin:userauth_forumuser_changelist")

    def form_valid(self, form):
        users = form.cleaned_data["users"]
        subject = form.cleaned_data["subject"]
        message_markdown = form.cleaned_data["message"]
        message_html = markdownify(message_markdown)
        if settings.DEBUG:
            emails_list = [
                "style.daniel@gmail.com",
            ]
        else:
            emails_list = [u.email for u in users]
        # Send emails
        email = EmailMultiAlternatives(subject, message_markdown, to=emails_list)
        email.attach_alternative(message_html, "text/html")
        email.send()
        # email_users.delay(users, subject, message)
        user_message = "{0} users emailed successfully!".format(form.cleaned_data["users"].count())
        messages.success(self.request, user_message)
        return super(SendUserEmails, self).form_valid(form)


@admin.action(description="Deactivate selected users")
def deactivate_users(self, request, queryset):
    for u in queryset:
        Follow.objects.filter(user=u).delete()
    queryset.update(is_active=False)


@admin.action(description="Make selected users moderators")
def action_grant_moderator(self, request, queryset):
    for u in queryset:
        if u.is_active:
            grant_moderator(u, 0, None)
        else:
            messages.warning(request, f"User {u} is inactive and can't be moderator")


@admin.action(description="Disable notifications for users")
def action_disable_notifications(self, request, queryset):
    queryset.update(email_notifications=False)
    messages.info(request, f"Disabled notifications for {queryset.count()} users")


@admin.action(description="Enable notifications for users")
def action_enable_notifications(self, request, queryset):
    queryset.update(email_notifications=True)
    messages.info(request, f"Enabled notifications for {queryset.count()} users")


@admin.action(description="Cleanup old users' visits")
def action_user_visits_cleanup(self, request, queryset):
    deleted = 0
    for u in queryset:
        last_visit = UserVisit.objects.filter(user=u).order_by("-visit_date").first()
        if last_visit is not None:
            count, _ = UserVisit.objects.filter(user=u, visit_date__lt=last_visit.visit_date).delete()
            deleted += count

    messages.info(request, f"Deleted {deleted} old visits")


@admin.action(description="Cleanup all users' visits")
def action_visits_cleanup(self, request, queryset):
    deleted = 0
    users = ForumUser.objects.all()
    for u in users:
        last_visit = UserVisit.objects.filter(user=u).order_by("-visit_date").first()
        if last_visit is not None:
            count, _ = UserVisit.objects.filter(user=u, visit_date__lt=last_visit.visit_date).delete()
            deleted += count

    messages.info(request, f"Deleted {deleted} old visits")
