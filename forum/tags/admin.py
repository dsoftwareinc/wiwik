from datetime import timedelta

from django.contrib import admin
from django.db.models import Count
from django.utils import timezone

from tags.models import Tag, Synonym, TagEdit


class QuestionInline(admin.TabularInline):
    extra = 0
    can_delete = True
    model = Tag.question_set.through
    ordering = ('question__id',)
    fields = ('question',)
    raw_id_fields = ('question',)


class SynonymInline(admin.TabularInline):
    extra = 0
    can_delete = True
    model = Synonym
    ordering = ('-created_at',)
    fields = ('name', 'author', 'created_at', 'active', 'approved_by',)
    raw_id_fields = ('author', 'approved_by',)
    readonly_fields = ('created_at',)


class TagEditInline(admin.TabularInline):
    extra = 0
    can_delete = True
    model = TagEdit
    ordering = ('-created_at',)
    fields = ('tag', 'author', 'created_at', 'summary',)
    raw_id_fields = ('author',)
    readonly_fields = ('created_at',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('tag_word', 'description', 'author__username',)
    list_display = ('id', 'tag_word', 'number_followers',
                    'questions_count', 'questions_last_week',
                    'synonym_count',
                    'related', 'experts', 'stars',
                    'created_at', 'author', 'description',
                    )
    fields = ('tag_word', 'description', 'author', 'wiki',
              ('number_of_questions', 'number_asked_today', 'number_asked_this_week',
               'number_followers'),
              ('related',),
              ('experts', 'stars',),
              'updated_at',
              )
    inlines = [SynonymInline, TagEditInline, QuestionInline, ]
    readonly_fields = ('number_of_questions', 'number_asked_today', 'number_asked_this_week',
                       'number_followers', 'updated_at',)

    def get_queryset(self, request):
        qs = super(TagAdmin, self).get_queryset(request)
        qs = (qs.annotate(
            questions_count=Count('question'),
            synonym_count=Count('synonym')))
        return qs

    @admin.display(ordering='questions_count', description='# questions')
    def questions_count(self, tag) -> int:
        return tag.questions_count

    @admin.display(ordering='synonym_count', description='# synonyms')
    def synonym_count(self, tag) -> int:
        return tag.synonym_count

    @admin.display(description='Qs last week')
    def questions_last_week(self, tag: Tag) -> int:
        aweek_ago = timezone.now() - timedelta(days=7)
        return tag.question_set.filter(created_at__gte=aweek_ago).count()


@admin.register(Synonym)
class SynonymAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'tag', 'author', 'created_at', 'active',)
    list_editable = ('active',)
    fields = ('name', 'tag', 'author', 'active',)
    raw_id_fields = ('tag', 'author',)
    list_filter = ('active',)


@admin.register(TagEdit)
class TagEditAdmin(admin.ModelAdmin):
    list_display = ('tag', 'author', 'created_at', 'summary',)
    fields = (('tag', 'author', 'created_at',),
              ('summary',),
              'before_description', 'before_wiki',)
    raw_id_fields = ('tag', 'author',)
    readonly_fields = ('created_at',)
