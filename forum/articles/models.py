from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from forum import jobs
from forum.jobs.populate_meilisearch import add_meilisearch_document, delete_meilisearch_document
from forum.models import Question, QuestionManager


class ArticleManager(QuestionManager):

    def get_queryset(self, *args, **kwargs):
        qs = super(QuestionManager, self).get_queryset(*args, **kwargs)
        qs = qs.filter(type__in=Question.POST_ARTICLE_TYPES)
        return qs


class Article(Question):
    objects = ArticleManager()

    class Meta:
        proxy = True
        verbose_name = "Article"


@receiver(post_save, sender=Article)
def create_meilisearch_doc(sender, instance, created, **kwargs):
    jobs.start_job(add_meilisearch_document, instance.id)


@receiver(pre_delete, sender=Article)
def delete_meilisearch_doc(sender, instance, **kwargs):
    jobs.start_job(delete_meilisearch_document, instance.id)
