from django.contrib import admin
from issuer.models import EarnerNotification


admin.site.register(EarnerNotification, admin.ModelAdmin)
