from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin

from .models import BadgeUser


class BadgeUserAdmin(ModelAdmin):
    readonly_fields = ('date_joined', 'last_login', 'username', )
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'last_login', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    fieldsets = (
        ('Metadata', {'fields': ('username', 'last_login', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name', )}),
        ('Access', {'fields': ('is_active', 'is_staff', 'is_superuser', 'password')}),
        ('Permissions', {'fields': ('groups','user_permissions')}),
    )
    pass

badgr_admin.register(BadgeUser, BadgeUserAdmin)
