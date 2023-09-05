from django.contrib import admin

from forum.apps import logger
from forum.models import TagFollow
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
        for q in tag.question_set.all():
            q.tags.remove(tag)
            q.tags.add(target_tag)
            q.save()
        for follow in tag.tagfollow_set.all():
            follow.tag = target_tag
            follow.save()
        for synonym in tag.synonym_set.all():
            synonym.tag = target_tag
            synonym.save()


admin.site.unregister(Tag)


class TagFollowInlineAdmin(admin.TabularInline):
    extra = 0
    model = TagFollow
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
    inlines = TagAdmin.inlines + [TagFollowInlineAdmin, ]
