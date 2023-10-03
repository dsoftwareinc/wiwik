from django.contrib import admin

from forum.apps import logger
from forum.models import UserTagStats
from tags.admin import TagAdmin
from tags.models import Tag


@admin.action(description='Merge tags')
def merge_tags(self, request, queryset):
    # Find tag with most questions
    results = list(queryset.order_by('-questions_count').values_list('tag_word', flat=True))
    logger.info(f'Got request to merge tags {results} to {results[0]}')
    target_tag = Tag.objects.get(tag_word=results[0])
    for tag_word in results[1:]:
        tag = Tag.objects.get(tag_word=tag_word)
        qs = tag.question_set.all()
        for q in qs:
            q.tags.remove(tag)
            q.tags.add(target_tag)
            q.save()
        qs = tag.usertagstats_set.all()
        for follow in qs:
            follow.tag = target_tag
            follow.save()
        qs = tag.synonym_set.all()
        for synonym in qs:
            synonym.tag = target_tag
            synonym.save()
        qs = tag.tagedit_set.all()
        for tagedit in qs:
            tagedit.tag = target_tag
            tagedit.save()
        user = tag.author
        tag.delete()
        target_tag.synonym_set.create(name=tag_word, author=user)


admin.site.unregister(Tag)


class UserTagStatsInlineAdmin(admin.TabularInline):
    extra = 0
    model = UserTagStats
    can_delete = True
    ordering = ('-created_at',)
    fields = ('tag', 'user', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('tag', 'user',)


@admin.register(Tag)
class ForumTagAdmin(TagAdmin):
    actions = [
        merge_tags,
    ]
    inlines = TagAdmin.inlines + [UserTagStatsInlineAdmin, ]
