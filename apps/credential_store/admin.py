from django.contrib import admin

from .models import (StoredBadgeInstance, StoredBadgeClass, StoredIssuer)


admin.site.register(StoredBadgeInstance, admin.ModelAdmin)
admin.site.register(StoredBadgeClass, admin.ModelAdmin)
admin.site.register(StoredIssuer, admin.ModelAdmin)
