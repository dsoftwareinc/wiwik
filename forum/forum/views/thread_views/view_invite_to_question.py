from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse

from forum.apps import logger
from forum.models import Question
from forum.views import utils
from userauth.models import ForumUser


@login_required
def view_users_autocomplete(request):
    if request.method != 'GET':
        raise Http404()
    qs = ForumUser.objects.all()
    query = request.GET.get('q', None)
    selected = request.GET.get('selected', None)
    selected = selected.split(',') if selected is not None else []
    if query is not None:
        qs = qs.filter(Q(username__icontains=query) | Q(name__icontains=query) | Q(email__icontains=query)) \
            .exclude(username=request.user, username__in=selected, is_superuser=True, is_active=False)
    results = list(qs.values('username', 'name', 'email', 'profile_pic'))[:(10 + len(selected))]
    for result in results:
        if result['profile_pic'][0] != '/':
            result['profile_pic'] = '/' + result['profile_pic']
        result['value'] = result['username']
    results = results[:10]
    return JsonResponse({'results': results})


@login_required
def view_invite_to_question(request, question_pk: int):
    if request.method != "POST":
        logger.warning("Someone is trying to make a request not through the app")
        return redirect('forum:thread', pk=question_pk)
    inviter = request.user
    invitee_usernames = request.POST.dict()['usernames']
    invitee_usernames = invitee_usernames.split(',')
    question = Question.objects.filter(pk=question_pk).first()
    if question is None:
        logger.warning(f'{inviter.username} is trying to invite users "{invitee_usernames}" '
                       f'to question {question_pk} which does not exist')
        return redirect(reverse('forum:thread', args=[question_pk]))
    invitees = (ForumUser.objects
                .filter(username__in=invitee_usernames)
                .exclude(username=question.author.username))
    count = utils.create_invites_and_notify_invite_users_to_question(inviter, invitees, question)
    logger.debug(f"Inviting users to question succeeded: {inviter.username}:invited {invitee_usernames}")
    if count > 0:
        messages.success(request, "Successfully invited user(s) to this question.")
    return redirect(reverse('forum:thread', args=[question_pk]))
