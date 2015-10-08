from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin

from .models import Issuer, BadgeClass, BadgeInstance


class IssuerAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by')
    list_display = ('img', 'name', 'slug', 'created_by', 'created_at')
    list_display_links = ('img', 'name')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug')
    fieldsets = (
        ('Metadata', {'fields': ('created_by', 'created_at', 'owner'), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'name', 'slug')}),
        ('JSON', {'fields': ('json',)}),
    )

    def img(self, obj):
        try:
            return u'<img src="{}" width="32"/>'.format(obj.image.url)
        except ValueError:
            return obj.image
    img.short_description = 'Image'
    img.allow_tags = True

badgr_admin.register(Issuer, IssuerAdmin)


class BadgeClassAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by')
    list_display = ('badge_image', 'name', 'slug', 'issuer')
    list_display_links = ('badge_image', 'name')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug', 'issuer__name',)
    fieldsets = (
        ('Metadata', {'fields': ('created_by', 'created_at',), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'name', 'slug', 'issuer')}),
        ('Criteria', {'fields': ('criteria_text',)}),
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
    fieldsets = (
        ('Metadata', {'fields': ('created_by', 'created_at',), 'classes': ("collapse",)}),
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
