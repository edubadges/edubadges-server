from django.contrib import admin

from lti_edu.models import LtiPayload, StudentsEnrolled, LtiClient, ResourceLinkBadge
from mainsite.admin import badgr_admin


@admin.register(LtiPayload)
class LtiPayloadAdmin(admin.ModelAdmin):
    list_display = ['date_created', 'data']


badgr_admin.register(LtiPayload, LtiPayloadAdmin)


@admin.register(ResourceLinkBadge)
class ResourceLinkBadgeAdmin(admin.ModelAdmin):
    list_display = ['date_created', 'resource_link', 'issuer', 'badge_class']


badgr_admin.register(ResourceLinkBadge, ResourceLinkBadgeAdmin)


@admin.register(StudentsEnrolled)
class StudentsEnrolledAdmin(admin.ModelAdmin):
    list_display = ['date_created', 'date_consent_given', 'date_awarded', 'assertion_slug', 'badge_class',
                    'email', 'first_name', 'last_name']


badgr_admin.register(StudentsEnrolled, StudentsEnrolledAdmin)


@admin.register(LtiClient)
class LtiClientAdmin(admin.ModelAdmin):
    list_display = ['date_created', 'is_active', 'name', 'issuer', 'consumer_key', 'shared_secret']


badgr_admin.register(LtiClient, LtiClientAdmin)
