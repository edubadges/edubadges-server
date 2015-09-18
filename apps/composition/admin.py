from django.contrib import admin

from .models import (Collection, LocalBadgeInstanceCollection,
                     LocalBadgeInstance, LocalBadgeClass, LocalIssuer,)


admin.site.register(Collection, admin.ModelAdmin)
admin.site.register(LocalBadgeInstanceCollection, admin.ModelAdmin)
admin.site.register(LocalBadgeInstance, admin.ModelAdmin)
admin.site.register(LocalBadgeClass, admin.ModelAdmin)
admin.site.register(LocalIssuer, admin.ModelAdmin)
