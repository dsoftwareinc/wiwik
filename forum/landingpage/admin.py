from django.contrib import admin

from landingpage.models import Lead


# Register your models here.
@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'email', 'message')
