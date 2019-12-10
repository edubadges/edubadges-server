from django.contrib import admin
from mainsite.admin import badgr_admin, FilterByScopeMixin

from .models import Institution, Faculty


class InstitutionAdmin(admin.ModelAdmin):
    pass


class FacultyAdmin(FilterByScopeMixin, admin.ModelAdmin):
    
    list_display = ('name', 'institution')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(FacultyAdmin, self).get_form(request, obj, **kwargs)
        institution = request.user.institution
        if institution:
            form.base_fields['institution'].initial = institution.id
        return form
    
    def filter_queryset_institution(self, queryset, request):
        institution_id = request.user.institution.id
        return queryset.filter(institution_id=institution_id).distinct()
     
    def filter_queryset_faculty(self, queryset, request):
        return queryset.filter(faculty__in=request.user.faculty.all()).distinct()
     
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "institution":
            if not request.user.is_superuser:
                kwargs["queryset"] = Institution.objects.filter(id=request.user.institution.id)
            else:
                kwargs["queryset"] = Institution.objects.all()
        return super(FacultyAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)         

badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)