from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Max
from django.utils.translation import gettext_lazy as _
from rangefilter.filters import DateRangeFilter

from forum.models import VoteActivity
from userauth.models import ForumUser, UserVisit
from userauth.utils import user_most_active_tags
from . import actions


class ActivityInline(admin.TabularInline):
    extra = 0
    model = VoteActivity
    fk_name = 'target'
    fields = ('badge', 'target', 'created_at',)
    readonly_fields = ('created_at', 'badge',)

    def get_queryset(self, request):
        qs = super(ActivityInline, self).get_queryset(request)
        return qs.filter(badge__isnull=False)


@admin.register(ForumUser)
class ForumUserAdmin(UserAdmin):
    search_fields = ('username', 'name', 'email', 'title',)
    list_display = ('username', 'name', 'email', 'title', 'date_joined', 'reputation_score',
                    'is_moderator', 'is_active', 'email_notifications', 'slack_userid',
                    'last_visit_date', 'active_tag_words', 'search_count', 'bookmarks_count',
                    'badges', 'people_reached', 'posts_edited', 'votes',)
    list_filter = ('is_moderator', 'is_staff', 'is_active', 'email_notifications',)
    fieldsets = ((None, {'fields': ('username', 'name', 'email', 'password')}),
                 (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
                 (_('Permissions'),
                  {'fields': ('is_moderator', 'is_active', 'is_staff',
                              'is_superuser',)}
                  ),
                 ('additional',
                  {'fields': ('reputation_score',
                              ('search_count', 'bookmarks_count', 'last_email_datetime',),
                              ('bronze_badges', 'silver_badges', 'gold_badges',),
                              ('people_reached', 'posts_edited', 'votes',),)}),
                 ('extra',
                  {'fields': ('profile_pic', 'title', 'about_me',
                              'slack_userid', 'email_notifications',)}),
                 )
    readonly_fields = ('last_login', 'date_joined', 'last_email_datetime', 'search_count', 'bookmarks_count',)
    save_on_top = True
    inlines = (ActivityInline,)

    actions = [
        actions.send_email,
        actions.deactivate_users,
        actions.action_grant_moderator,
        actions.action_user_visits_cleanup,
        actions.action_disable_notifications,
        actions.action_enable_notifications,
    ]

    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        return (qs.annotate(last_visit_date=Max('uservisit__visit_date')))

    def active_tag_words(self, o: ForumUser):
        return ', '.join(user_most_active_tags(o))

    @admin.display(description='Last visit', ordering='last_visit_date')
    def last_visit_date(self, o: ForumUser):
        return o.last_visit_date


@admin.register(UserVisit)
class UserVisitAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'ip_addr', 'visit_date', 'country', 'city',
        'consecutive_days', 'max_consecutive_days', 'total_days',
    )
    list_filter = (
        ('visit_date', DateRangeFilter),
        'country',
    )
    fields = (
        'user', 'ip_addr', 'visit_date', 'country', 'city',
        'consecutive_days', 'total_days', 'max_consecutive_days',
    )
    save_on_top = True
    search_fields = ('country', 'city', 'user__username', 'user__email', 'ip_addr', 'visit_date',)
    autocomplete_fields = ('user',)
    actions = [
        actions.action_visits_cleanup,
    ]
