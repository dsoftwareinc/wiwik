from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from forum.models import QuestionBookmark


@admin.register(QuestionBookmark)
class QuestionBookmarkAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "question",
        "user",
        "created_at",
    )
    raw_id_fields = (
        "question",
        "user",
    )
    list_filter = (("created_at", DateRangeFilter),)
