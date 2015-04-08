from django.contrib import admin

from .models import BadgeUser


admin.site.register(BadgeUser, admin.ModelAdmin)
