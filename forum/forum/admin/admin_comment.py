from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.safestring import mark_safe

from forum.models import QuestionComment, AnswerComment
from wiwik_lib.models import Flag


class FlagInline(GenericTabularInline):
    model = Flag
    extra = 0
    fields = ('user', 'flag_type', 'created_at',)
    readonly_fields = ('created_at',)


@admin.register(QuestionComment)
class QuestionCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'parent_id', 'content',)
    fields = ('author', 'content', 'created_at', 'question',)
    search_fields = ('author__username', 'author__email', 'question__title',)
    autocomplete_fields = ('author', 'question',)
    readonly_fields = ('created_at',)
    inlines = [FlagInline, ]

    @admin.display(ordering='question__id')
    def parent_id(self, obj):
        base_url = reverse('admin:forum_question_changelist')
        pid = obj.question.id
        return mark_safe(f'<a href="{base_url}?id={pid}">Q{pid}</a>')


@admin.register(AnswerComment)
class AnswerCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'parent_id', 'content',)
    fields = ('author', 'content', 'created_at', 'answer',)
    search_fields = ('author__username', 'author__email',)
    autocomplete_fields = ('author',)
    raw_id_fields = ('answer',)
    readonly_fields = ('created_at',)
    inlines = [FlagInline, ]

    @admin.display(ordering='answer__id')
    def parent_id(self, obj):
        base_url = reverse('admin:forum_answer_changelist')
        pid = obj.answer.id
        return mark_safe(f'<a href="{base_url}?id={pid}">Q{pid}</a>')
