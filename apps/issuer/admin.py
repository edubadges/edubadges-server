import basic_models
from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin

from .models import Issuer, BadgeClass, BadgeInstance


class IssuerAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by')
    list_display = ('name', 'slug', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug')
    fieldsets = (
        ('Meta', {'fields': ('created_by', 'created_at', 'owner'), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'name', 'slug')}),
        ('JSON', {'fields': ('json',)}),
    )
badgr_admin.register(Issuer, IssuerAdmin)


class BadgeClassAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by')
    list_display = ('badge_image', 'name', 'slug', 'issuer')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug', 'issuer__name',)
    actions_on_top = True
    fieldsets = (
        ('Meta', {'fields': ('created_by', 'created_at',), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'name', 'slug', 'criteria_text')}),
        ('JSON', {'fields': ('json',)}),
    )

    def badge_image(self, obj):
        return u'<img src="{}" width="32"/>'.format(obj.image.url)
    badge_image.short_description = 'Badge'
    badge_image.allow_tags = True

badgr_admin.register(BadgeClass, BadgeClassAdmin)


class BadgeInstanceAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'image', 'slug')
    list_display = ('badge_image', 'recipient_identifier', 'slug', 'badgeclass', 'issuer')
    list_display_links = ('badge_image', 'recipient_identifier', )
    list_filter = ('created_at',)
    search_fields = ('slug', 'badgeclass__name', 'issuer__name')
    actions_on_top = True
    fieldsets = (
        ('Meta', {'fields': ('created_by', 'created_at',), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'slug', 'recipient_identifier', 'badgeclass', 'issuer')}),
        ('Revocation', {'fields': ('revoked', 'revocation_reason')}),
        ('JSON', {'fields': ('json',)}),
    )

    def badge_image(self, obj):
        try:
            return u'<img src="{}" width="32"/>'.format(obj.image.url)
        except ValueError:
            return obj.image
    badge_image.short_description = 'Badge'
    badge_image.allow_tags = True

    def has_add_permission(self, request):
        return False

badgr_admin.register(BadgeInstance, BadgeInstanceAdmin)
