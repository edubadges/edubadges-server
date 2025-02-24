# mypy: ignore-errors
from django.contrib import admin

from mainsite.admin import badgr_admin
from mainsite.utils import admin_list_linkify
from .models import DirectAward, DirectAwardBundle


class DirectAwardAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient_email', 'eppn', 'created_at', admin_list_linkify('badgeclass', 'name'),
                    'institution_identifier', 'status')
    list_display_links = ('recipient_email', 'eppn')
    list_filter = ('created_at', 'badgeclass__name', 'badgeclass__issuer__faculty__institution__identifier')
    search_fields = ('recipient_email', 'eppn', 'badgeclass__name',)

    @admin.display(
        description='Institution',
        ordering='badgeclass__issuer__faculty__institution__identifier',
    )
    def institution_identifier(self, obj):
        return obj.badgeclass.issuer.faculty.institution.identifier



class DirectAwardBundleAdmin(admin.ModelAdmin):
    list_display = (
        'assertion_count', 'direct_award_count', 'direct_award_rejected_count',
        'direct_award_scheduled_count','direct_award_revoked_count',
        'created_at', admin_list_linkify('badgeclass', 'name'), 'institution_identifier')

    list_filter = ('created_at', 'badgeclass__issuer__faculty__institution__identifier')
    search_fields = ('badgeclass__name',)

    @admin.display(
        description='Institution',
        ordering='badgeclass__issuer__faculty__institution__identifier',
    )
    def institution_identifier(self, obj):
        return obj.badgeclass.issuer.faculty.institution.identifier



badgr_admin.register(DirectAward, DirectAwardAdmin)
badgr_admin.register(DirectAwardBundle, DirectAwardBundleAdmin)
