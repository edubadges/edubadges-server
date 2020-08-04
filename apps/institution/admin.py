from django.contrib import admin
from mainsite.admin import badgr_admin
from .models import Institution, Faculty


class InstitutionAdmin(admin.ModelAdmin):
    readonly_fields = ('entity_id', 'created_by', 'updated_by')
    list_display = ('name', 'identifier', 'brin')


class FacultyAdmin(admin.ModelAdmin):
    
    list_display = ('name',)
    readonly_fields = ('entity_id', 'created_by', 'updated_by', 'institution')


badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)