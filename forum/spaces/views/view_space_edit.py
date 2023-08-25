from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import UpdateView

from forum.models import Question
from spaces.models import Space
from spaces.views.access import validate_space_access


class SpaceUpdateView(UpdateView):
    model = Space
    fields = ['name', 'page', 'start_date', 'end_date', 'properties', 'logo', ]
    template_name = 'spaces/space-edit2.html'


@login_required
def view_space_edit(request, space_id: int):
    space = get_object_or_404(Space, id=space_id)
    validate_space_access(space, request.user)
    is_member = space.spacemember_set.filter(user=request.user).exists()
    if request.method == 'POST':
        if not is_member:
            raise PermissionDenied('Only members can edit space info')
        data = request.POST.dict()
        space.page = data.get('page') or space.page
        space.save()
        return redirect('spaces:detail', space_id=space_id)
    members = space.spacemember_set.all()
    latest_posts = Question.objects.filter(space=space).order_by('-created_at')[:5]

    return render(request, 'spaces/space-edit.html', {
        'space': space,
        'is_member': is_member,
        'members': members,
        'latest_posts': latest_posts,
    })
