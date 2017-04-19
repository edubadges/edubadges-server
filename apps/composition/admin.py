from django.contrib.admin import ModelAdmin, TabularInline

from mainsite.admin import badgr_admin
from composition.models import (Collection, LocalBadgeInstance, )


###
#
# Local Issuer/Badges
#
###


class LocalBadgeInstanceAdmin(ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'image', )
    list_display = ('badge_image', 'recipient_identifier', 'issuer_badgeclass',)
    list_display_links = ('badge_image', 'recipient_identifier', )
    list_filter = ('created_at',)
    search_fields = ('issuer_badgeclass__name',)
    fieldsets = (
        ('Metadata', {'fields': ('created_by', 'created_at',), 'classes': ()}),
        (None, {'fields': ('image', 'recipient_identifier', 'issuer_badgeclass', 'issuer')}),
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

