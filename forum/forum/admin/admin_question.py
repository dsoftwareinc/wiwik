from admin_numeric_filter.admin import SliderNumericFilter, NumericFilterModelAdmin
from django.contrib import admin
from rangefilter.filters import DateRangeFilter

from forum.admin.input_filter import UserFilter
from forum.models import Question, Answer, QuestionComment, QuestionFollow, \
    PostInvitation


class QuestionFollowInline(admin.TabularInline):
    extra = 0
    model = QuestionFollow
    readonly_fields = ('created_at', 'user')
    search_fields = ('user__username', 'user__email')
    autocomplete_fields = ('user',)


class QuestionCommentInline(admin.TabularInline):
    extra = 0
    model = QuestionComment
    readonly_fields = ('created_at',)
    search_fields = ('author__username', 'author__email')
    autocomplete_fields = ('author',)
    raw_id_fields = ('users_upvoted',)


class AnswerInline(admin.TabularInline):
    extra = 0
    model = Answer
    fields = ('created_at', 'author', 'editor', 'content', 'is_accepted', 'users_upvoted', 'users_downvoted',)
    search_fields = ('author__username', 'author__email',)
    autocomplete_fields = ('author', 'editor',)
    raw_id_fields = ('users_upvoted', 'users_downvoted',)
    readonly_fields = ('created_at',)


class QuestionInviteToAnswerInline(admin.TabularInline):
    extra = 0
    model = PostInvitation
    search_fields = ('invitee__username', 'invitee__email',)
    autocomplete_fields = ('invitee', 'inviter', 'question',)
    fields = ('created_at', 'question', 'invitee', 'inviter',)
    readonly_fields = ('created_at',)


@admin.register(Question)
class QuestionAdmin(NumericFilterModelAdmin):
    list_display = ('id', 'type', 'status', 'title', 'author', 'views', 'votes',
                    'bookmarks_count', 'answers_count', 'followers_count',
                    'has_accepted_answer', 'is_anonymous', 'space',
                    'last_activity', 'created_at', 'updated_at', 'status_updated_at',
                    'tags_list',)
    fields = ('type', 'title',
              'content',
              ('author', 'editor', 'tags', 'space',),
              ('has_accepted_answer', 'is_anonymous',),
              ('status', 'status_updated_at'),
              ('views', 'source', 'source_id', 'link',),
              ('users_upvoted', 'users_downvoted',),
              ('last_activity', 'created_at', 'updated_at', 'bookmarks_count',),)
    readonly_fields = ('last_activity', 'created_at', 'updated_at', 'bookmarks_count',)
    raw_id_fields = ('author', 'tags', 'users_upvoted', 'users_downvoted', 'space',)
    list_filter = (
        'type',
        UserFilter,
        ('created_at', DateRangeFilter),
        ('votes', SliderNumericFilter),
        'status',
        'has_accepted_answer', 'is_anonymous',)
    search_fields = ('title', 'author__username', 'content',)
    inlines = (
        AnswerInline, QuestionCommentInline,
        QuestionFollowInline, QuestionInviteToAnswerInline,)
    save_on_top = True

    @admin.display(description='#Bookmarks', )
    def bookmarks_count(self, o: Question):
        return o.bookmarks.count()

    @admin.display(description='#Followers', )
    def followers_count(self, o: Question):
        return QuestionFollow.objects.filter(question=o).count()

    @admin.display(description='Tags List', )
    def tags_list(self, o: Question):
        return u", ".join(o.tag_words())


@admin.register(PostInvitation)
class QuestionInviteToAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'invitee', 'inviter', 'created_at',)
    raw_id_fields = ('question', 'invitee', 'inviter',)
    list_filter = (('created_at', DateRangeFilter),)
    search_fields = ('question__title', 'question__id', 'invitee__username',
                     'invitee__email', 'inviter__username', 'inviter__email',)
