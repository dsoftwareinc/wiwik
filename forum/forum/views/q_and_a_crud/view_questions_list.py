from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect

from forum.models import Question
from forum.views import utils
from forum.views.helpers import render_questions
from tags.models import Tag


@login_required
def view_questions(request):
    tag_user_follows = utils.get_user_followed_tags(request.user)
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    q = utils.get_request_param(request, 'q', None)
    header = 'All questions' if q is None else 'Search results'
    return render_questions(
        request, Question.objects, header, {'tags_watched': tag_words_user_follows, })


@login_required
def view_home(request):
    main_query = Question.objects
    tag_user_follows = utils.get_user_followed_tags(request.user)
    if len(tag_user_follows) == 0:
        messages.info(
            request,
            'You need to follow tags so your home page will be adjusted for you, '
            'meanwhile you can see all the questions in the forum')
        return redirect('forum:list')
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    main_query = main_query.filter(tags__tag_word__in=tag_words_user_follows).distinct().order_by('-last_activity')
    return render_questions(request, main_query, 'Home', {'tags_watched': tag_words_user_follows, })


@login_required
def view_tag_questions_list(request, tag_word: str):
    tag = Tag.objects.filter(tag_word=tag_word).first()
    if tag is None:
        messages.warning(request, f'Tag {tag_word} does not exist')
        return redirect('forum:list')
    main_query = Question.objects.filter(Q(tags__tag_word__iexact=tag_word))
    show_edit_desc_button = request.user.can_edit_tag
    tag_user_follows = utils.get_user_followed_tags(request.user)
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    return render_questions(
        request, main_query, f'Questions tagged [{tag_word}]', {
            'tag': tag,
            'can_edit_tag': show_edit_desc_button,
            'tags_watched': tag_words_user_follows,
        }
    )
