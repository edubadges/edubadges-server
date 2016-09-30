from django.contrib.admin import ModelAdmin, TabularInline
from mainsite.admin import badgr_admin
from issuer.admin import IssuerAdmin, BadgeClassAdmin

from .models import (Collection, LocalBadgeInstanceCollection,
                     LocalBadgeInstance, LocalBadgeClass, LocalIssuer,)

###
#
# Local Issuer/Badges
#
###


class LocalIssuerAdmin(IssuerAdmin):
    readonly_fields = ('created_at',)
    list_display = ('img', 'name', 'slug', 'created_by', 'created_at')
    fieldsets = (
        ('Metadata', {'fields': ('created_at',), 'classes': ("collapse",)}),
        (None, {'fields': ('image', 'name', 'slug', 'created_by')}),
        ('JSON', {'fields': ('json',)}),
    )

    def img(self, obj):
        return u'<img src="{}" width="32"/>'.format(obj.image_preview.url) if obj.image_preview else ''
    img.short_description = 'Image'
    img.allow_tags = True
badgr_admin.register(LocalIssuer, LocalIssuerAdmin)


class LocalBadgeClassAdmin(BadgeClassAdmin):
    readonly_fields = ('created_at',)
    list_display = ('img', 'name', 'slug', 'issuer')
    list_display_links = ('img', 'name')

    def img(self, obj):
        return u'<img src="{}" width="32"/>'.format(obj.image_preview.url) if obj.image_preview else ''
    img.short_description = 'Image'
    img.allow_tags = True
badgr_admin.register(LocalBadgeClass, LocalBadgeClassAdmin)


class LocalBadgeInstanceAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'image', )
    list_display = ('badge_image', 'recipient_identifier', 'badgeclass', 'issuer')
    list_display_links = ('badge_image', 'recipient_identifier', )
    list_filter = ('created_at',)
    search_fields = ('badgeclass__name', 'issuer__name')
    fieldsets = (
        ('Metadata', {'fields': ('created_by', 'created_at',), 'classes': ()}),
        (None, {'fields': ('image', 'recipient_identifier', 'badgeclass', 'issuer')}),
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
    readonly_fields = ('created_at',)


badgr_admin.register(LocalBadgeInstance, LocalBadgeInstanceAdmin)




###
#
# Collection
#
###

class CollectionInstanceInline(TabularInline):
    model = Collection.instances.through
    extra = 0
    raw_id_fields = ('instance','issuer_instance',)


class CollectionSharedInline(TabularInline):
    model = Collection.shared_with.through
    extra = 0


class CollectionAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'owner',)
    search_fields = ('owner__email', 'name', 'slug')
    raw_id_fields = ('owner',)
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'owner', 'share_hash')}),
    )
    inlines = [
        CollectionInstanceInline,
        CollectionSharedInline,
    ]
    pass
badgr_admin.register(Collection, CollectionAdmin)



