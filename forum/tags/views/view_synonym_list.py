from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse

from badges.jobs import review_bagdes_event
from badges.logic.utils import TRIGGER_EVENT_TYPES
from forum import jobs
from tags import models
from tags.apps import logger
from tags.models import Synonym

ITEMS_PER_PAGE = 15


def create_new_suggestion(request, synonym_name: str, tag_word: str):
    if not synonym_name or not tag_word:
        messages.warning(request, "Can not create empty synonym")
        return
    if " " in synonym_name:
        messages.warning(request, "Synonym name should not contain spaces")
        return
    tag = models.Tag.objects.filter(tag_word=tag_word).first()
    if tag is None:
        messages.warning(request, "Could not find this tag, first ask a few questions with it")
        return
    if tag.synonym_set.filter(name=synonym_name).exists():
        messages.warning(request, "Synonym with this name already suggested for this tag, aborting")
        return
    if Synonym.objects.filter(name=synonym_name).exists():
        messages.warning(
            request,
            "Synonym with this name already suggested for another tag, aborting",
        )
        return
    tag.synonym_set.create(name=synonym_name, author=request.user)


ORDER_BY_MAP = {
    1: "name",
    2: "tag__tag_word",
    3: "author__username",
    4: "created_at",
    5: "active",
}


def _get_order_by_from_request(request):
    try:
        order_by_num = int(request.GET.get("order_by", "-4"))
    except ValueError:
        order_by_num = -5
    order_by = (
        ORDER_BY_MAP.get(order_by_num, "created_at")
        if order_by_num > 0
        else ("-" + ORDER_BY_MAP.get(-order_by_num, "created_at"))
    )
    return order_by, order_by_num


@login_required
def view_synonym_list(request):
    if request.method == "POST":
        req_dict = request.POST.dict()
        synonym_name = req_dict.get("synonym", "").lower()
        tag_word = req_dict.get("tag", "").lower()
        create_new_suggestion(request, synonym_name, tag_word)
    query = request.GET.get("q", "")
    page = request.GET.get("page", 1)
    basic_query_set = models.Synonym.objects.all()
    if query:
        basic_query_set = basic_query_set.filter(Q(name__icontains=query) | Q(tag__tag_word__icontains=query))
    order_by, order_by_num = _get_order_by_from_request(request)
    basic_query_set = basic_query_set.order_by(order_by)
    paginator = Paginator(basic_query_set, ITEMS_PER_PAGE)
    items = paginator.get_page(page)

    return render(
        request,
        "tags/synonym_list.html",
        {
            "items": items,
            "can_approve": request.user.can_approve_synonym,
            "order_by": order_by_num,
            "query": query,
            "page": page,
            "title": "wiwik - Synonyms",
        },
    )


@login_required
def view_approve_synonym(request, synonym_pk: int):
    synonym = models.Synonym.objects.filter(pk=synonym_pk).first()
    if synonym is None:
        logger.warning(f"user {request.user.username} tries to approve non existing synonym {synonym_pk}")
        return redirect(reverse("tags:synonyms_list"))
    user = request.user
    if user.can_approve_synonym:
        messages.info(request, f"Synonym {synonym.name} approved")
        logger.info(f"user {request.user.username} approved {synonym.name} for tag {synonym.tag.tag_word}")
        synonym.active = True
        synonym.approved_by = user
        synonym.save()
        jobs.start_job(review_bagdes_event, TRIGGER_EVENT_TYPES["Synonym approved"])
    else:
        logger.warning(
            f"user {request.user.username} tried to approve synonym "
            f"{synonym.name} for tag {synonym.tag.tag_word} but lacks permissions"
        )
    return redirect(reverse("tags:synonyms_list"))
