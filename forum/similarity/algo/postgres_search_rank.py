from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramDistance
from django.db.models import F

from forum import models


def postgres_search_rank(text: str, q: models.Question) -> float:
    """
    Calculate postgres full text search rank between text and question search vector.
    higher rank => better match.
    """
    search_query = SearchQuery(text)
    search_rank = SearchRank(F('additional_data__search_vector'), search_query)
    rank = (models.Question.objects.filter(id=q.id)
            .annotate(rank=search_rank)
            .values_list('rank', flat=True)
            .first())
    return rank


def postgres_trigram_rank(text: str, q: models.Question) -> float:
    """
    Calculate postgres trigram rank between text and question title+content.
    rank is calculated as 1-distance, i.e., higher rank => better match.
    """
    title_weight = settings.POSTGRES_SEARCH['weights']['title']
    content_weight = settings.POSTGRES_SEARCH['weights']['content']
    distance = (models.Question.objects.filter(id=q.id)
                .annotate(title_distance=TrigramDistance('title', text))
                .annotate(content_distance=TrigramDistance('content', text))
                .annotate(relevance=1 - F('title_distance') * title_weight - F('content_distance') * content_weight)
                .order_by('-relevance')
                .values_list('relevance', flat=True)
                .first())
    return 1 - distance
