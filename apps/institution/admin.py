from django.contrib import admin
from mainsite.admin import badgr_admin
from .models import Institution, Faculty
from badgeuser.admin import TermsInline
from mainsite.utils import admin_list_linkify


class InstitutionAdmin(admin.ModelAdmin):
    readonly_fields = ('entity_id', 'created_by', 'updated_by')
    list_display = ('name', 'identifier', 'brin')

    inlines = [TermsInline]


class FacultyAdmin(admin.ModelAdmin):
    
    list_display = ('name',)
    readonly_fields = ('entity_id', 'created_by', 'updated_by', 'institution')
    list_display = ('name', 'entity_id', admin_list_linkify('institution', 'name'))


badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)