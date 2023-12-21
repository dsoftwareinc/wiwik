from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from forum.jobs import start_job
from forum.models import Question
from similarity.calculate_similarity_job import calculate_similarity_for_question


class PostSimilarity(models.Model):
    question1 = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    question2 = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    postgres_rank = models.DecimalField(max_digits=5, decimal_places=4, help_text="Postgres full text search rank")
    postgres_trigram_rank = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        help_text="Reverse of distance based on trigram similarity",
    )
    tfidf_rank = models.DecimalField(max_digits=5, decimal_places=4, help_text="TF-IDF similarity")
    rank = models.DecimalField(max_digits=5, decimal_places=4, help_text="Calculated rank")

    class Meta:
        verbose_name_plural = "Similar Posts"

    def __str__(self):
        return (
            f"Similiarity {self.question1.id}-{self.question2.id}="
            f"(postgres_rank={self.postgres_rank},tfidf_rank={self.tfidf_rank})"
        )


@receiver(post_save, sender=Question)
def calc_similarity_signal(sender, instance, created, **kwargs):
    if created:
        start_job(calculate_similarity_for_question, instance)
