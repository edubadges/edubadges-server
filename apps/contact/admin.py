from django.contrib import admin
from contact.models import Submission


admin.site.register(Submission, admin.ModelAdmin)