from django.contrib import admin
from django.db.models import Q
from rangefilter.filters import DateRangeFilter

from forum.admin.input_filter import InputFilter
from forum.models import UserTagStats


class TagNameFilter(InputFilter):
    parameter_name = 'tag__tag_word'
    title = 'Tag name'

    def queryset(self, request, queryset):
        if self.value() is not None:
            val = self.value()

            return queryset.filter(
                Q(tag__tag_word__icontains=val)
            )


@admin.register(UserTagStats)
class UserTagStatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'tag_word', 'created_at', 'updated_at',
                    'questions_by_user', 'answers_by_user', 'reputation',
                    'reputation_last_month',)
    list_filter = (TagNameFilter,
                   ('created_at', DateRangeFilter),
                   )
    search_fields = ('user__username', 'user__email', 'tag__tag_word',)
    autocomplete_fields = ('user',)

    @admin.display(description='Tag name', ordering='tag__tag_word')
    def tag_word(self, o):
        return o.tag.tag_word
