from django.contrib import admin

from .models import (Collection, StoredBadgeInstanceCollection,)


admin.site.register(Collection, admin.ModelAdmin)
admin.site.register(StoredBadgeInstanceCollection, admin.ModelAdmin)
