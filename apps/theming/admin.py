from django.contrib import admin
from .models import Theme
from mainsite.admin import badgr_admin


class ThemeAdmin(admin.ModelAdmin):
    pass


badgr_admin.register(Theme, ThemeAdmin)
