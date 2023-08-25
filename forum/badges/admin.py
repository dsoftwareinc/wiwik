from django.contrib import admin
from django.db.models import Count
from rangefilter.filters import DateRangeFilter

from badges.models import Badge
from forum.models import VoteActivity


class ActivityInline(admin.TabularInline):
    extra = 0
    model = VoteActivity
    fields = ('badge', 'target', 'created_at',)
    readonly_fields = ('created_at',)
    search_fields = ('target__username',)
    autocomplete_fields = ('target',)


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'description', 'section',)
    list_display = ('id', 'name', 'description', 'section', 'type', 'trigger', 'users_earned',
                    'only_once', 'active', 'created_at',)
    fields = ('name', 'description', 'section', 'type', 'trigger',
              'only_once', 'active', 'created_at',)
    readonly_fields = ('created_at',)
    list_filter = ('section',
                   'type',
                   'active',
                   'only_once',
                   'trigger',
                   ('created_at', DateRangeFilter),
                   )
    inlines = (ActivityInline,)

    def get_queryset(self, request):
        qs = super(BadgeAdmin, self).get_queryset(request)
        qs = qs.annotate(activity_count=Count('voteactivity'), )
        return qs

    @admin.display(ordering='activity_count')
    def users_earned(self, o: Badge) -> int:
        return o.activity_count
