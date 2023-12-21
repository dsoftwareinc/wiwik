from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from tags import models


def get_tags_matching(query: str):
    qs = models.Tag.objects.all()
    if query is not None:
        qs = qs.filter(tag_word__icontains=query)
    results = list(
        qs.order_by("-number_asked_this_week").values_list("tag_word", flat=True)[:10]
    )
    if len(results) < 10 and query is not None:
        synonym_list = list(
            models.Synonym.objects.filter(active=True, name__icontains=query)
            .exclude(tag__tag_word__in=results)
            .order_by("-tag__number_asked_this_week")
            .values_list("name", flat=True)
            .distinct()[: 10 - len(results)]
        )
        results += synonym_list
    return results


@login_required
def view_tags_autocomplete(request):
    query = request.GET.get("q", None)
    results = get_tags_matching(query)
    return JsonResponse({"results": results})
