import json

from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from forum.apps import logger
from forum.integrations import slack_api
from forum.models import Question
from forum.views import search
from tags.views.view_tag_autocomplete import get_tags_matching


@csrf_exempt
def view_slack_post(request):
    if not slack_api.verify_request(request):
        return HttpResponseNotFound()
    if request.method != "POST":
        return HttpResponse(status=200)
    payload = json.loads(request.POST.dict()["payload"])
    slack_api.post_from_slack(payload)
    return HttpResponse(status=200)


@csrf_exempt
def view_tags_autocomplete_for_slack(request):
    if not slack_api.verify_request(request):
        return HttpResponseNotFound()
    if request.method != "POST":
        return HttpResponse(status=200)
    payload = json.loads(request.POST.dict()["payload"])
    tags_matching = get_tags_matching(payload["value"])
    options = [
        {
            "text": {
                "type": "plain_text",
                "text": tag_word,
            },
            "value": tag_word,
        }
        for tag_word in tags_matching
    ]
    return JsonResponse(data={"options": options})


@csrf_exempt
def search_from_slack(request):
    if not slack_api.verify_request(request):
        return HttpResponseNotFound()
    if request.method != "POST":
        return HttpResponse(status=200)
    # user_id = request.POST.get('user_id', None)
    query = request.POST.get("text", None)
    results = list(
        search.query_method(Question.objects, query).order_by("-has_accepted_answer", "-votes", "-created_at")[:3]
    )
    res = {"blocks": slack_api.questions_message(results)}
    logger.debug(res)
    return JsonResponse(data=res, status=200)
