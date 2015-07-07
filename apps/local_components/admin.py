from django.contrib import admin

from .models import (BadgeInstance, BadgeClass, Issuer)


admin.site.register(BadgeInstance, admin.ModelAdmin)
admin.site.register(BadgeClass, admin.ModelAdmin)
admin.site.register(Issuer, admin.ModelAdmin)
