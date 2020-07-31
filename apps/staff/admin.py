from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class InstitutionStaffAdmin(ModelAdmin):

    list_display = ('user', 'institution_name', 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')

    def institution_name(self, obj):
        return obj.institution.name


class FacultyStaffAdmin(ModelAdmin):

    list_display = ('user', 'faculty_name', 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')

    def faculty_name(self, obj):
        return obj.faculty.name


class IssuerStaffAdmin(ModelAdmin):

    list_display = ('user', 'issuer_name', 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')

    def issuer_name(self, obj):
        return obj.issuer.name


class BadgeclassStaffAdmin(ModelAdmin):

    list_display = ('user', 'badgeclass_name', 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')

    def badgeclass_name(self, obj):
        return obj.badgeclass.name


badgr_admin.register(InstitutionStaff, InstitutionStaffAdmin)
badgr_admin.register(FacultyStaff, FacultyStaffAdmin)
badgr_admin.register(IssuerStaff, IssuerStaffAdmin)
badgr_admin.register(BadgeClassStaff, BadgeclassStaffAdmin)