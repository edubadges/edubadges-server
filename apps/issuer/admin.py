from django.contrib import admin

from .models import Issuer, BadgeClass, BadgeInstance


admin.site.register(Issuer, admin.ModelAdmin)
admin.site.register(BadgeClass, admin.ModelAdmin)
admin.site.register(BadgeInstance, admin.ModelAdmin)
