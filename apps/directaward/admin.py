# mypy: ignore-errors
from django.contrib import admin

from mainsite.admin import badgr_admin
from mainsite.utils import admin_list_linkify
from .models import DirectAward, DirectAwardBundle


class DirectAwardAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient_email', 'eppn', admin_list_linkify('badgeclass', 'name'), 'status')


class DirectAwardBundleAdmin(admin.ModelAdmin):
    list_display = (
    'assertion_count', 'direct_award_count', 'direct_award_rejected_count', 'direct_award_revoked_count',
    admin_list_linkify('badgeclass', 'name'))


badgr_admin.register(DirectAward, DirectAwardAdmin)
badgr_admin.register(DirectAwardBundle, DirectAwardBundleAdmin)
