from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from rangefilter.filters import DateRangeFilter

from articles.models import Article
from forum.admin.input_filter import UserFilter
from wiwik_lib.models import Follow


@admin.register(Article)
class ArticleAdmin(NumericFilterModelAdmin):
    list_display = (
        "id",
        "type",
        "status",
        "title",
        "author",
        "views",
        "votes",
        "bookmarks_count",
        "followers_count",
        "last_activity",
        "created_at",
        "updated_at",
        "status_updated_at",
        "tags_list",
    )
    fields = (
        "type",
        "title",
        "content",
        (
            "author",
            "editor",
            "tags",
            "space",
        ),
        ("status", "status_updated_at"),
        (
            "users_upvoted",
            "users_downvoted",
        ),
        (
            "last_activity",
            "created_at",
            "updated_at",
            "bookmarks_count",
        ),
    )
    readonly_fields = (
        "last_activity",
        "created_at",
        "updated_at",
        "bookmarks_count",
    )
    raw_id_fields = (
        "author",
        "tags",
        "users_upvoted",
        "users_downvoted",
        "space",
    )
    list_filter = (
        UserFilter,
        ("created_at", DateRangeFilter),
        ("votes", SliderNumericFilter),
        "status",
    )
    search_fields = (
        "title",
        "author__username",
        "content",
    )

    @admin.display(
        description="#Bookmarks",
    )
    def bookmarks_count(self, o: Article):
        return o.bookmarks.count()

    @admin.display(
        description="#Followers",
    )
    def followers_count(self, o: Article):
        return Follow.objects.filter(content_type=ContentType.objects.get_for_model(o), object_id=o.id).count()

    @admin.display(
        description="Tags List",
    )
    def tags_list(self, o: Article):
        return ", ".join(o.tag_words())
