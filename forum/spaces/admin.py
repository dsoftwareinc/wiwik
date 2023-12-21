from django.contrib import admin
from django.db.models import Count
from rangefilter.filters import DateRangeFilter

from forum.models import Question
from spaces.models import Space, SpaceMember, SpaceProperty, SpaceToProperty


class QuestionInline(admin.TabularInline):
    extra = 1
    model = Question
    fk_name = "space"
    ordering = ("-created_at",)
    can_delete = False
    fields = (
        "space",
        "title",
        "author",
        "created_at",
    )
    show_change_link = True
    readonly_fields = (
        "title",
        "author",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False


class SpaceMemberInline(admin.TabularInline):
    extra = 0
    can_delete = True
    model = SpaceMember
    ordering = ("-created_at",)
    fields = (
        "user",
        "space",
        "created_at",
    )
    readonly_fields = ("created_at",)
    raw_id_fields = (
        "user",
        "space",
    )


class SpaceToPropertyInline(admin.TabularInline):
    extra = 0
    can_delete = True
    model = SpaceToProperty
    ordering = ("-space__created_at",)
    raw_id_fields = (
        "space",
        "property",
    )
    verbose_name = "Space - Property"
    verbose_name_plural = "Space - Property matches"


@admin.register(Space)
class SpaceAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = (
        "id",
        "short_name",
        "name",
        "restricted",
        "start_date",
        "end_date",
        "space_active",
        "properties_str",
        "author",
        "created_at",
    )
    list_display_links = (
        "id",
        "short_name",
        "name",
    )
    search_fields = (
        "name",
        "author",
    )
    list_filter = (
        ("created_at", DateRangeFilter),
        "restricted",
    )
    inlines = [
        SpaceToPropertyInline,
        SpaceMemberInline,
        QuestionInline,
    ]
    fields = (
        ("short_name", "name", "logo", "author"),
        (
            "start_date",
            "end_date",
        ),
        ("restricted",),
        ("page",),
    )
    raw_id_fields = ("author",)
    readonly_fields = ("created_at",)

    def properties_str(self, o: Space):
        return ",".join([p.name for p in o.properties.all()])


@admin.register(SpaceProperty)
class SpacePropertyAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "created_at",
        "spaces_count",
    )
    list_display_links = (
        "id",
        "name",
    )
    raw_id_fields = ("author",)
    search_fields = (
        "name",
        "author__username",
        "author__email",
    )
    list_filter = (("created_at", DateRangeFilter),)
    readonly_fields = ("created_at",)
    inlines = [
        SpaceToPropertyInline,
    ]

    def get_queryset(self, request):
        qs = super(SpacePropertyAdmin, self).get_queryset(request)
        qs = qs.annotate(
            spaces_count=Count("spaces"),
        )
        return qs

    @admin.display(ordering="spaces_count")
    def spaces_count(self, o):
        return o.spaces_count
