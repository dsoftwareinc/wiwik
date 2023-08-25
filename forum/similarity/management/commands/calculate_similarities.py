from django.core.management.base import BaseCommand

from forum.models import Question
from similarity.calculate_similarity_job import calculate_similarity_for_pair


class Command(BaseCommand):
    help = 'Calculate similarities between all different questions'

    def handle(self, *args, **options):
        question_qs = Question.objects.all().order_by('id')
        # calculate_tfidf()
        for q1 in question_qs:
            newer_questions_qs = Question.objects.filter(id__gt=q1.id)
            for q2 in newer_questions_qs:
                # sim1 = sentence_similarity(q1.title, q2.title, False)
                # sim2 = sentence_similarity(q1.title, q2.title, True)
                # print("---%s\n---%s\n---%.3f\t%.3f\n" % (q1.title, q2.title, sim1, sim2))
                calculate_similarity_for_pair(q1, q2)
