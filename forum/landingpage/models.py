from django.db import models


# Create your models here.
class Lead(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()
    message = models.TextField()
