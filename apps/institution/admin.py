from django.contrib import admin
from mainsite.admin import badgr_admin
from .models import Institution, Faculty


class InstitutionAdmin(admin.ModelAdmin):
    pass


class FacultyAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'institution')


badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)