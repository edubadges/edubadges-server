from django.contrib.admin import ModelAdmin
from mainsite.admin import badgr_admin
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff

class InstitutionStaffAdmin(ModelAdmin):

    list_display = ('user', 'institution', 'create', 'read', 'update',
                    'destroy', 'award', 'sign', 'administrate_users')

class FacultyStaffAdmin(ModelAdmin):

    list_display = ('user', 'faculty', 'create', 'read', 'update',
                    'destroy', 'award', 'sign', 'administrate_users')

class IssuerStaffAdmin(ModelAdmin):

    list_display = ('user', 'issuer', 'create', 'read', 'update',
                    'destroy', 'award', 'sign', 'administrate_users')

class BadgeclassStaffAdmin(ModelAdmin):

    list_display = ('user', 'badgeclass', 'create', 'read', 'update',
                    'destroy', 'award', 'sign', 'administrate_users')

badgr_admin.register(InstitutionStaff, InstitutionStaffAdmin)
badgr_admin.register(FacultyStaff, FacultyStaffAdmin)
badgr_admin.register(IssuerStaff, IssuerStaffAdmin)
badgr_admin.register(BadgeClassStaff, BadgeclassStaffAdmin)