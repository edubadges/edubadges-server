# encoding: utf-8
from __future__ import unicode_literals

from django.contrib.admin import ModelAdmin, TabularInline

from externaltools.models import ExternalTool, ExternalToolLaunchpoint
from mainsite.admin import badgr_admin


class LaunchpointInline(TabularInline):
    model = ExternalToolLaunchpoint
    extra = 0
    fields = ('launchpoint', 'label', 'launch_url', 'icon_url')


class ExternalToolAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'entity_id')
    list_display = ('name', 'entity_id', 'config_url', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'config_url', 'xml_config', 'client_id')
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at', 'entity_id'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('is_active', 'requires_user_activation', 'name', 'config_url', 'client_id', 'client_secret')
        }),
        ('Config', {
            'fields': ('xml_config',)
        })
    )
    inlines = [
        LaunchpointInline
    ]


badgr_admin.register(ExternalTool, ExternalToolAdmin)
