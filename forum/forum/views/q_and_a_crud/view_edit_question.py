from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from forum.models import Question
from forum.views import utils
from wiwik_lib.views import ask_to_edit_resource, finish_edit_resource
from .view_ask_question import validate_question_data, QuestionError


@login_required
def view_editquestion(request, pk):
    user = request.user
    q = get_object_or_404(Question, pk=pk)
    if q.author != user and not user.can_edit:  # TODO change edit user permissions
        messages.error(request, 'You can not edit this question', 'danger')
        return redirect('forum:thread', pk=pk)
    if not ask_to_edit_resource(request.user, q):
        messages.warning(request, 'Question is currently edited by a different user')
        return redirect('forum:thread', pk=pk)
    title = q.title
    content = q.content
    tags = ','.join(q.tag_words())
    # Update question
    if request.method == 'POST':
        questiontaken = request.POST.dict()
        title = questiontaken.get('title')
        content = questiontaken.get('queseditor')
        tags = questiontaken.get('tags') or ''
        try:
            validate_question_data(title, content)
            finish_edit_resource(q)
            utils.update_question(user, q, title, content, tags)
            messages.success(request, 'Question updated successfully')
            return redirect('forum:thread', pk=pk)
        except QuestionError as e:
            messages.warning(request, f'Error: {e}')
    # Request to edit
    return render(request, 'main/editquestion.html', {
        'title': title,
        'content': content,
        'tags': tags,
        'question_pk': pk,
    })
