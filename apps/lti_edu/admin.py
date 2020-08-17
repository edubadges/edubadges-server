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
    list_display = ['date_created', 'date_consent_given', 'date_awarded', 'badge_instance', 'badge_class',
                    'email', 'user']


badgr_admin.register(StudentsEnrolled, StudentsEnrolledAdmin)


@admin.register(LtiClient)
class LtiClientAdmin(admin.ModelAdmin):
    list_display = ['date_created', 'is_active', 'name', 'issuer', 'consumer_key', 'shared_secret']


badgr_admin.register(LtiClient, LtiClientAdmin)




class IMSArchiveAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at', 'metadata_tag')


class LTIAppAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'description', 'privacy_level', 'created_at', 'modified_at')


class LTITenantAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'client_key', 'client_secret', 'get_lti_config_url', 'created_at', 'modified_at')
    prepopulated_fields = {'slug': ('organization',)}


# badgr_admin.register(IMSArchive, IMSArchiveAdmin)
# badgr_admin.register(LTIApp, LTIAppAdmin)
# badgr_admin.register(LTITenant, LTITenantAdmin)


