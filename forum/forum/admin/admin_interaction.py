from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from forum.models import VoteActivity, SearchRecord


@admin.register(VoteActivity)
class ActivityAdmin(NumericFilterModelAdmin):
    list_display = (
        'id', 'target',
        'cause', 'impact',
        'source', 'question_id', 'answer_id',
        'created_at', 'seen',
    )
    fields = (('target', 'source', 'created_at',),
              ('question', 'answer',),
              ('reputation_change', 'badge',),
              'seen',
              )
    readonly_fields = ('created_at',)
    search_fields = ('target__username', 'target__email', 'source__username',
                     'source__email', 'question__title',)
    autocomplete_fields = ('source', 'target', 'question',)
    raw_id_fields = ('answer', 'badge',)
    list_filter = (('created_at', DateRangeFilter),
                   ('reputation_change', SliderNumericFilter),
                   ('seen', DateRangeFilter),
                   'badge',
                   )

    @admin.display(description='Impact', ordering='reputation_change')
    def impact(self, o: VoteActivity):
        return o.badge.name if o.badge else o.reputation_change

    def cause(self, o: VoteActivity):
        return o.question.title if o.question else 'Badge'


@admin.register(SearchRecord)
class SearchRecordAdmin(admin.ModelAdmin):
    search_fields = ('query', 'author__username', 'author__email',)
    list_display = ('id', 'query', 'results', 'time', 'author', 'created_at',)
    list_filter = (('created_at', DateRangeFilter),
                   ('time', SliderNumericFilter),
                   )
