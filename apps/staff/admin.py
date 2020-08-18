from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin
from mainsite.utils import admin_list_linkify
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class InstitutionStaffAdmin(ModelAdmin):

    list_display = ('user', admin_list_linkify('institution', 'name'), 'may_create',
                    'may_read', 'may_update', 'may_delete', 'may_award', 'may_sign', 'may_administrate_users')


class FacultyStaffAdmin(ModelAdmin):

    list_display = ('user', admin_list_linkify('faculty', 'name'), 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')


class IssuerStaffAdmin(ModelAdmin):

    list_display = ('user', admin_list_linkify('issuer', 'name'), 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')


class BadgeclassStaffAdmin(ModelAdmin):

    list_display = ('user', admin_list_linkify('badgeclass', 'name'), 'may_create', 'may_read', 'may_update',
                    'may_delete', 'may_award', 'may_sign', 'may_administrate_users')


badgr_admin.register(InstitutionStaff, InstitutionStaffAdmin)
badgr_admin.register(FacultyStaff, FacultyStaffAdmin)
badgr_admin.register(IssuerStaff, IssuerStaffAdmin)
badgr_admin.register(BadgeClassStaff, BadgeclassStaffAdmin)