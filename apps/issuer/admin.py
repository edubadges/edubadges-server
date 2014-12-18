from django.contrib import admin
from issuer.models import EarnerNotification
from client_admin.admin import ClientModelAdmin


admin.site.register(EarnerNotification, ClientModelAdmin)
