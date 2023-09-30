from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from scheduler import job

from forum.models import Question
from forum.views import thread_markdown_bytesio
from similarity import algo
from similarity import models
from similarity.algo.tfidf import calc_tfidf_pair, calc_tfidf_multiple_documents
from similarity.apps import logger

KNOWN_SIMILARITIES = {'postgres_rank', 'postgres_trigram_rank', 'tfidf_rank'}
SIMILARITY_THRESHOLD = 0.2


def _upsert_similarity(q1: Question, q2: Question, **kwargs):
    """
    Create or update a new Similarity object with
    """
    similarities = kwargs
    if len(similarities.keys()) == 0:
        logger.warning("No similarities were given, give one of " + ', '.join(KNOWN_SIMILARITIES))
        return
    remove_keys = []
    for k, v in similarities.items():
        if v is None:
            remove_keys.append(k)
        if k not in KNOWN_SIMILARITIES:
            logger.warning(f"{k} not in known similarities ({', '.join(KNOWN_SIMILARITIES)})")
            return
    for k in remove_keys:
        similarities.pop(k)
    sim = (models.PostSimilarity.objects
           .filter(Q(question1=q1, question2=q2) | Q(question1=q2, question2=q1))
           .first())
    if sim is None:
        sim = models.PostSimilarity.objects.create(question1=q1,
                                                   question2=q2,
                                                   rank=0,
                                                   tfidf_rank=0,
                                                   postgres_rank=0,
                                                   postgres_trigram_rank=0)
    for k, v in similarities.items():
        logger.debug(f'Updating similarity {q1.id} <> {q2.id}: {k}={v:5.4}')
        setattr(sim, k, v)
    sim.rank = (float(sim.tfidf_rank) + float(sim.postgres_rank)) / 2
    if sim.rank < SIMILARITY_THRESHOLD:
        logger.info('Deleting low similarity')
        sim.delete()
        return
    sim.updated_at = timezone.now()
    sim.save()


def calculate_tfidf():
    docs = list()
    question_ids = list()
    question_qs = Question.objects.all()
    for q in question_qs:
        q_doc = thread_markdown_bytesio(q, include_authors=False).getvalue().decode('utf8')
        docs.append(q_doc)
        question_ids.append(q.id)
    res = calc_tfidf_multiple_documents(docs)
    for i in range(len(question_ids)):
        for j in range(i, len(question_ids)):
            if i == j:
                continue
            q1 = Question.objects.get(id=question_ids[i])
            q2 = Question.objects.get(id=question_ids[j])
            _upsert_similarity(q1, q2, tfidf_rank=res[i][j])


@job
def calculate_similarity_for_question(q: Question):
    if settings.DATABASES['default']['ENGINE'] != "django.db.backends.postgresql":
        return
    question_qs = Question.objects.exclude(id=q.id)
    for q2 in question_qs:
        calculate_similarity_for_pair(q, q2)


@job
def calculate_similarity_for_pair(post1_id: Question, post2_id: Question) -> None:
    if post1_id == post2_id:
        logger.debug('Not calculating similarity for same question')
        return
    post1_id, post2_id = (post1_id,post2_id) if post1_id<post2_id else (post2_id, post1_id)
    q1 = Question.objects.filter(id=post1_id).first()
    q2 = Question.objects.filter(id=post2_id).first()
    if q1 is None or q2 is None:
        logger.debug(f'Could not find posts with IDs {post1_id}/{post2_id}.')
        return
    q1_str = thread_markdown_bytesio(q1).getvalue().decode('utf8')
    q2_str = thread_markdown_bytesio(q2).getvalue().decode('utf8')
    tfidf = calc_tfidf_pair(q1_str, q2_str)
    fts_rank, trigram_rank = None, None
    if settings.DATABASES['default']['ENGINE'] == "django.db.backends.postgresql":
        fts_rank = algo.postgres_search_rank(q1.title, q2)
        trigram_rank = algo.postgres_trigram_rank(q1.title, q2)

    _upsert_similarity(q1, q2, postgres_rank=fts_rank, postgres_trigram_rank=trigram_rank, tfidf_rank=tfidf)
