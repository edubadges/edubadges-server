from django.contrib.admin import ModelAdmin, TabularInline

from mainsite.admin import badgr_admin
from .models import (BackpackCollection, )


###
#
# Collection
#
###


class CollectionInstanceInline(TabularInline):
    model = BackpackCollection.assertions.through
    extra = 0
    raw_id_fields = ('badgeinstance',)


class CollectionAdmin(ModelAdmin):
    list_display = ('created_by', 'name', 'entity_id', )
    search_fields = ('created_by__email', 'name', 'entity_id')
    fieldsets = (
        (None, {'fields': ('created_by', 'name', 'entity_id', 'description', 'share_hash')}),
    )
    readonly_fields = ('created_by',)
    inlines = [
        CollectionInstanceInline,
    ]
    pass
badgr_admin.register(BackpackCollection, CollectionAdmin)
