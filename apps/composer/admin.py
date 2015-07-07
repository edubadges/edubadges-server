from django.contrib import admin

from .models import (Collection, LocalBadgeInstanceCollection,)


admin.site.register(Collection, admin.ModelAdmin)
admin.site.register(LocalBadgeInstanceCollection, admin.ModelAdmin)
