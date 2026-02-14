from django.contrib import admin
from .models import MobileDevice, MobileAPIRequestLog


@admin.register(MobileDevice)
class MobileDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'device_type', 'device_model', 'app_version', 'os_version', 'created_at', 'last_seen')
    list_filter = ('device_type', 'created_at')
    search_fields = ('device_id', 'device_model', 'app_version')
    readonly_fields = ('created_at', 'last_seen')
    fieldsets = (
        (None, {'fields': ('device_id', 'device_type', 'device_model')}),
        ('Version Information', {'fields': ('app_version', 'os_version')}),
        ('Timestamps', {'fields': ('created_at', 'last_seen'), 'classes': ('collapse',)}),
    )


@admin.register(MobileAPIRequestLog)
class MobileAPIRequestLogAdmin(admin.ModelAdmin):
    list_display = ('method', 'endpoint', 'status_code', 'response_time_ms', 'timestamp', 'device', 'user')
    list_filter = ('method', 'status_code', 'endpoint', 'timestamp')
    search_fields = ('endpoint', 'user_agent', 'ip_address')
    readonly_fields = ('timestamp', 'response_time_ms')
    fieldsets = (
        (None, {'fields': ('method', 'endpoint', 'status_code')}),
        ('Performance', {'fields': ('response_time_ms',)}),
        ('Device & User', {'fields': ('device', 'user')}),
        ('Client Information', {'fields': ('ip_address', 'user_agent')}),
        ('Timestamps', {'fields': ('timestamp',), 'classes': ('collapse',)}),
    )
    date_hierarchy = 'timestamp'
