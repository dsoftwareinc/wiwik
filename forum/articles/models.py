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
        verbose_name = "Articles"
