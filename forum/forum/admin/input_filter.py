from django.contrib import admin
from django.db.models import Q


class InputFilter(admin.SimpleListFilter):
    template = "admin/input_filter.html"

    def lookups(self, request, model_admin):
        # required to show the filter.
        return ((),)

    def choices(self, changelist):
        # Grab only the "all" option.
        all_choice = next(super().choices(changelist))
        all_choice["query_parts"] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )
        yield all_choice


class UserFilter(InputFilter):
    parameter_name = "author__username"
    title = "Username"

    def queryset(self, request, queryset):
        if self.value() is not None:
            name = self.value()

            return queryset.filter(Q(author__username__icontains=name))


class QuestionFilter(InputFilter):
    parameter_name = "question__id"
    title = "Question ID"

    def queryset(self, request, queryset):
        if self.value() is not None:
            q_id = self.value()

            return queryset.filter(Q(question__id=q_id))


class QuestionFollowUserFilter(InputFilter):
    parameter_name = "user__username"
    title = "Username"

    def queryset(self, request, queryset):
        name = self.value()
        if name is not None:
            return queryset.filter(Q(user__username__icontains=name))
