from django.contrib import admin

from lti_edu.models import LtiPayload, StudentsEnrolled, LtiClient, ResourceLinkBadge
from mainsite.admin import badgr_admin, FilterByScopeMixin
from issuer.models import Issuer


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
                    'email', 'first_name', 'last_name']


badgr_admin.register(StudentsEnrolled, StudentsEnrolledAdmin)


@admin.register(LtiClient)
class LtiClientAdmin(FilterByScopeMixin, admin.ModelAdmin):
    list_display = ['date_created', 'is_active', 'name', 'issuer', 'consumer_key', 'shared_secret']
    
    def filter_queryset_institution(self, queryset, request):
        institution_id = request.user.institution.id
        return queryset.filter(issuer__faculty__institution_id=institution_id).distinct()
    
    def filter_queryset_faculty(self, queryset, request):
        return queryset.filter(issuer__faculty__in=request.user.faculty.all()).distinct()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "issuer":
            if not request.user.is_superuser:
                if request.user.has_perm(u'badgeuser.has_institution_scope'):
                    institution_id = request.user.institution.id
                    kwargs["queryset"] = Issuer.objects.filter(faculty__institution_id=institution_id)
                elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
                    kwargs["queryset"] = Issuer.objects.filter(faculty__in=request.user.faculty.all()).distinct()
                else:
                    kwargs["queryset"] = Issuer.objects.none()
        return super(LtiClientAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


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


