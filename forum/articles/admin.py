from admin_numeric_filter.admin import NumericFilterModelAdmin, SliderNumericFilter
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from articles.models import Article
from forum.admin.input_filter import UserFilter
from forum.models import QuestionFollow


@admin.register(Article)
class ArticleAdmin(NumericFilterModelAdmin):
    list_display = ('id', 'type', 'status', 'title', 'author', 'views', 'votes',
                    'bookmarks_count', 'followers_count',
                    'last_activity', 'created_at', 'updated_at', 'status_updated_at',
                    'tags_list',)
    fields = ('type', 'title',
              'content',
              ('author', 'editor', 'tags', 'space',),
              ('status', 'status_updated_at'),
              ('users_upvoted', 'users_downvoted',),
              ('last_activity', 'created_at', 'updated_at', 'bookmarks_count',),)
    readonly_fields = ('last_activity', 'created_at', 'updated_at', 'bookmarks_count',)
    raw_id_fields = ('author', 'tags', 'users_upvoted', 'users_downvoted', 'space',)
    list_filter = (
        UserFilter,
        ('created_at', DateRangeFilter),
        ('votes', SliderNumericFilter),
        'status',
    )
    search_fields = ('title', 'author__username', 'content',)

    @admin.display(description='#Bookmarks', )
    def bookmarks_count(self, o: Article):
        return o.bookmarks.count()

    @admin.display(description='#Followers', )
    def followers_count(self, o: Article):
        return QuestionFollow.objects.filter(question=o).count()

    @admin.display(description='Tags List', )
    def tags_list(self, o: Article):
        return u", ".join(o.tag_words())
