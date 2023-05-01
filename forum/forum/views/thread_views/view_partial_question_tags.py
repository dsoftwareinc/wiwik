from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from forum.models import Question
from forum.views import utils


@login_required
def view_partial_question_tags(request, question_pk: int):
    q = get_object_or_404(Question, pk=question_pk)
    tag_user_follows = utils.get_user_followed_tags(request.user)
    tag_words_user_follows = [t.tag_word for t in tag_user_follows]
    return render(request, 'main/includes/partial.thread.question-tags.html', {
        'q': q,
        'tags_watched': tag_words_user_follows,
    })
