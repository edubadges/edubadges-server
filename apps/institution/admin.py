from django.contrib import admin
from .models import Institution, Faculty
from mainsite.admin import badgr_admin

class InstitutionAdmin(admin.ModelAdmin):
    pass

class FacultyAdmin(admin.ModelAdmin):
    pass

badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)