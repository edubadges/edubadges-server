from django.contrib import admin

from .models import (LocalBadgeInstance, LocalBadgeClass, LocalIssuer)


admin.site.register(LocalBadgeInstance, admin.ModelAdmin)
admin.site.register(LocalBadgeClass, admin.ModelAdmin)
admin.site.register(LocalIssuer, admin.ModelAdmin)
