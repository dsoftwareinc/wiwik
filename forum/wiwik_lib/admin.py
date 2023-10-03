from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from wiwik_lib.models import Flag, EditedResource, Follow


class ExtendableAdmin(admin.ModelAdmin):
    def content_object_url(self, obj) -> str:
        url = reverse(f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change', args=[obj.object_id])
        return mark_safe(f'<a href="{url}">{obj.content_object}</a>')

    def content_author(self, obj) -> str:
        return obj.content_object.author.email


@admin.register(Flag)
class FlagAdmin(ExtendableAdmin):
    list_display = ('id', 'user', 'flag_type', 'content_author',
                    'created_at',
                    'content_type', 'object_id', 'content_object_url',)
    list_filter = ('flag_type',)
    search_fields = ('user__username', 'user__email', 'flag_type',)
    autocomplete_fields = ('user',)
    readonly_fields = ('content_object', 'content_author',)


@admin.register(EditedResource)
class EditedResourceAdmin(ExtendableAdmin):
    list_display = ('id', 'user',
                    'created_at', 'last_ping_at',
                    'content_type', 'object_id', 'content_object_url',)
    search_fields = ('user__username', 'user__email',)
    autocomplete_fields = ('user',)
    readonly_fields = ('content_object', 'content_author',)


@admin.register(Follow)
class FollowAdmin(ExtendableAdmin):
    list_display = ('id', 'user', 'created_at', 'content_type', 'object_id', 'content_object_url',)
    search_fields = ('user__username', 'user__email',)
    autocomplete_fields = ('user',)
    readonly_fields = ('content_object', 'content_author',)
