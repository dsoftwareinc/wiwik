from constance import config
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.utils import timezone

from forum.apps import logger


# TODO prevent abuse
@login_required
def view_image_upload(request):
    if request.method != "POST" or not request.FILES["image"]:
        data = {"error": "noFileGiven"}
        return JsonResponse(data)
    upload = request.FILES["image"]
    if upload.size > config.MAX_SIZE_KB_IMAGE_UPLOAD_KB * 1024:
        data = {"error": "fileTooLarge"}
        return JsonResponse(data)
    filename = "uploads/" + timezone.now().strftime("%Y-%m-%d.%H-%M-%S") + "." + upload.name.split(".")[-1]
    logger.info(f"User {request.user} uploaded {upload.name}, saved as {filename}")
    fss = FileSystemStorage()
    file = fss.save(filename, upload)
    file_url = fss.url(file)
    data = {"data": {"filePath": file_url}}
    return JsonResponse(data)
