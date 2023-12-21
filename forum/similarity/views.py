from django.contrib.auth.decorators import login_required
from django.db.models import Q, OuterRef, Func, F, Subquery
from django.shortcuts import render, get_object_or_404

from forum.models import Question, Answer
from similarity import models


def most_similar_questions_by_postgres_rank(q: Question, count: int = 5):
    similarity_qs = (
        models.PostSimilarity.objects.filter(Q(question1=q) | Q(question2=q))
        .select_related(
            "question1",
            "question2",
            "question1__author",
            "question2__author",
        )
        .order_by("-rank")
        .values("question1_id", "question2_id")[:count]
    )
    question_ids = [
        similarity["question2_id"] if similarity["question1_id"] == q.id else similarity["question1_id"]
        for similarity in similarity_qs
    ]
    a_subquery = (
        Answer.objects.filter(question=OuterRef("pk"))
        .annotate(count=Func(F("id"), function="Count"))
        .values("count")
        .order_by("-count")
    )
    questions = Question.objects.filter(id__in=question_ids).annotate(num_answers=Subquery(a_subquery))
    return questions


@login_required
def view_partial_related_questions(request, question_pk: int):
    q = get_object_or_404(Question, pk=question_pk)
    related = most_similar_questions_by_postgres_rank(q)

    return render(request, "partial.thread.related-questions.template.html", {"related": related})
