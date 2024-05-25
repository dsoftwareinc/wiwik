import shlex

from constance import config
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramDistance
from django.db.models import CharField, Func, BigIntegerField
from django.db.models import QuerySet, Q, F, Value
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from forum import jobs
from forum.apps import logger
from forum.jobs.populate_meilisearch import (
    add_meilisearch_document,
    delete_meilisearch_document,
)
from forum.models import Question


def _postgres_enabled() -> bool:
    return settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"


def initial_query(qs: QuerySet, query: str):
    try:
        query_parts = shlex.split(query)
    except ValueError:
        query = query.replace('"', "'")
        if query.count("'") % 2 == 1:
            query += "'"
        query_parts = shlex.split(query)
    result_query = []
    for qpart in query_parts:
        if len(qpart) <= 1:
            continue
        elif qpart[0] == "[" and qpart[-1] == "]":
            tag_word = qpart[1:-1]
            qs = qs.filter(tags__tag_word__iexact=tag_word)
        elif qpart.startswith("user:"):
            username = qpart.split(":")[1]
            qs = qs.filter(author__username__icontains=username)
        elif qpart.startswith("answers:"):
            num_answers = int(qpart.split(":")[1])
            qs = qs.filter(answers_count=num_answers)
        elif qpart.startswith("score:"):
            try:
                score = int(qpart.split(":")[1])
            except ValueError:
                score = 0
            qs = qs.filter(votes__gte=score)
        elif qpart.startswith("resolved:"):
            val = qpart.split(":")[1] == "yes"
            qs = qs.filter(has_accepted_answer=val)
        elif qpart.startswith("space:"):
            space_name = qpart.split(":")[1]
            qs = qs.filter(space__short_name__iexact=space_name)
        else:
            result_query.append(qpart)
    qs = qs.order_by("-created_at")
    result_query = " ".join(result_query)
    logger.debug(f'Ran initial query with "{query}", result query is "{result_query}"')
    return qs, result_query


def sqlite3_query_method(qs: QuerySet, query: str) -> QuerySet:
    qs, query = initial_query(qs, query)
    return qs.filter(Q(title__icontains=query))


def postgres_query_method(qs: QuerySet, initial_q: str) -> QuerySet:
    qs, query = initial_query(qs, initial_q)
    if not query:
        return qs.annotate(relevance=Value(1))
    search_query = SearchQuery(query)
    search_rank = SearchRank(F("additional_data__search_vector"), search_query)
    res_qs = (
        qs.annotate(relevance=search_rank).filter(relevance__isnull=False, relevance__gt=0.1).order_by("-relevance")
    )
    if res_qs.count() == 0:
        title_weight = config.trigram_weight_title
        content_weight = config.trigram_weight_content
        res_qs = (
            qs.annotate(title_distance=TrigramDistance("title", query))
            .annotate(content_distance=TrigramDistance("content", query))
            .annotate(relevance=1 - F("title_distance") * title_weight - F("content_distance") * content_weight)
            .filter(relevance__gt=config.trigram_min_relevance)
            .order_by("-relevance")
        )
    return res_qs


class ArrayPosition(Func):
    function = "array_position"

    def __init__(self, items, *expressions, **extra):
        if isinstance(items[0], int):
            base_field = BigIntegerField()
        else:
            base_field = CharField(max_length=max(len(i) for i in items))
        first_arg = Value(list(items), output_field=ArrayField(base_field))
        expressions = (first_arg,) + expressions
        super().__init__(*expressions, **extra)


def meilisearchmethod():
    if (
            not settings.MEILISEARCH_ENABLED
            or not settings.MEILISEARCH_SERVER_ADDRESS
            or not settings.MEILISEARCH_MASTERKEY
    ):
        return ValueError("Can not use meilisearch when its configuration is off")
    import meilisearch

    client = meilisearch.Client(settings.MEILISEARCH_SERVER_ADDRESS, settings.MEILISEARCH_MASTERKEY)
    index = client.index("posts")

    def meilisearch(qs: QuerySet, initial_q: str):
        qs, query = initial_query(qs, initial_q)
        if not query:
            return qs.annotate(relevance=Value(1))
        meilisearch_response = index.search(
            query,
            {
                "attributesToRetrieve": ["id"],
                "limit": 20,
            },
        )
        question_ids = list(map(lambda x: x["id"], meilisearch_response["hits"]))

        qs = qs.filter(id__in=question_ids)
        if len(question_ids) > 0 and _postgres_enabled():
            qs = qs.annotate(ordering=ArrayPosition(question_ids, F("id"), output_field=BigIntegerField())).order_by(
                "ordering"
            )
        return qs

    return meilisearch


def configure_query_method():
    postgres_enabled = _postgres_enabled()
    logger.info(
        f"Determining search method, meilisearch={settings.MEILISEARCH_ENABLED},postgres_enabled={postgres_enabled}"
    )
    if settings.MEILISEARCH_ENABLED:
        logger.info("Meilisearch enabled, checking whether server is reachable")
        return meilisearchmethod()
    elif postgres_enabled:
        logger.info("Database engine is postgres, query method based on postgres full text search")
        assert config.trigram_min_relevance is not None
        assert config.trigram_weight_title is not None
        assert config.trigram_weight_content is not None
        res = postgres_query_method
    else:
        logger.warning("Database engine not postgres, defaulting to query method based on title only")
        res = sqlite3_query_method

    return res


query_method = configure_query_method()


@receiver(post_save, sender=Question)
def create_meilisearch_doc(sender, instance, created, **kwargs):
    jobs.start_job(add_meilisearch_document, instance.id)


@receiver(pre_delete, sender=Question)
def delete_meilisearch_doc(sender, instance, **kwargs):
    jobs.start_job(delete_meilisearch_document, instance.id)
