from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from rangefilter.filters import DateRangeFilter

from forum.admin.input_filter import UserFilter, QuestionFilter
from forum.models import Answer, AnswerComment

admin.site.login = login_required(admin.site.login)


class AnswerCommentInline(admin.TabularInline):
    extra = 0
    model = AnswerComment
    search_fields = ('author__username', 'author__email',)
    autocomplete_fields = ('author',)
    raw_id_fields = ('users_upvoted',)


@admin.register(Answer)
class AnswerAdmin(NumericFilterModelAdmin):
    list_display = ('id', 'question', 'author', 'is_accepted', 'votes', 'created_at',)
    fields = ('question', 'content', 'author',
              'is_accepted',
              ('users_upvoted', 'users_downvoted',),
              )
    search_fields = ('author__username', 'content', 'question__title')
    autocomplete_fields = ('author', 'question',)
    raw_id_fields = ('users_upvoted', 'users_downvoted')
    inlines = (AnswerCommentInline,)
    list_filter = (
        UserFilter, QuestionFilter,
        ('created_at', DateRangeFilter),
        ('votes', SliderNumericFilter),
        'is_accepted',)
