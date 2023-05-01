import base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.shortcuts import render, redirect


@login_required
def view_profile_pic(request):
    user = request.user
    if request.method == 'POST':
        image_data = request.POST.dict()['cropped-profile-pic']
        image_format, image_string = image_data.split(';base64,')
        extension = image_format.split('/')[-1]
        data = ContentFile(base64.b64decode(image_string))
        file_name = f'profile_pic_{user.username}.{extension}'
        user.profile_pic.save(file_name, data, save=True)

        messages.success(request, 'Profile updated successfully')
        return redirect('userauth:profile', username=user.username, tab='questions')
    return render(request, 'userauth/editprofile.html', {'user': user})
