from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from similarity.models import PostSimilarity


@admin.register(PostSimilarity)
class PostSimilarityAdmin(NumericFilterModelAdmin):
    list_display = (
        "id",
        "q1_id",
        "q2_id",
        "rank",
        "tfidf_rank",
        "postgres_rank",
        "postgres_trigram_rank",
        "created_at",
        "updated_at",
    )
    readonly_fields = (
        "question1",
        "question2",
        "rank",
        "tfidf_rank",
        "postgres_rank",
        "postgres_trigram_rank",
        "created_at",
        "updated_at",
    )
    list_filter = (
        ("created_at", DateRangeFilter),
        ("tfidf_rank", SliderNumericFilter),
        ("postgres_rank", SliderNumericFilter),
        ("postgres_trigram_rank", SliderNumericFilter),
    )

    def q1_id(self, o):
        return o.question1.id

    def q2_id(self, o):
        return o.question2.id
