from django.contrib import admin
from django.forms import ModelForm

from badgeuser.admin import TermsInline
from badgeuser.models import BadgeUser
from mainsite.admin import badgr_admin
from mainsite.utils import admin_list_linkify
from .models import Institution, Faculty


class InstitutionForm(ModelForm):
    class Meta:
        model = Institution
        exclude = ()

    def clean(self):
        sis_integration_enabled = self.cleaned_data.get('sis_integration_enabled', False)
        if sis_integration_enabled:
            sis_default_user = self.cleaned_data.get('sis_default_user', None)
            if not sis_default_user:
                self._errors['sis_default_user'] = self.error_class(['sis_default_user required for SIS integration'])
            manage_client_id = self.cleaned_data.get('manage_client_id', None)
            if not manage_client_id:
                self._errors['manage_client_id'] = self.error_class(['manage_client_id required for SIS integration'])
        return self.cleaned_data


class InstitutionAdmin(admin.ModelAdmin):
    readonly_fields = ('entity_id', 'created_by', 'updated_by')
    list_display = ('name_english', 'name_dutch', 'identifier', 'brin')
    form = InstitutionForm
    inlines = [TermsInline]

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if not obj:
            for attr in ['sis_integration_enabled', 'sis_default_user', 'manage_client_id']:
                fields.remove(attr)
        return fields

    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        if db_field.name == "sis_default_user":
            institution_id = request.resolver_match.kwargs.get('object_id')
            if institution_id:
                kwargs["queryset"] = BadgeUser.objects.filter(is_teacher=True, institution__id=institution_id)
        return super(InstitutionAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)


class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name_english', 'name_dutch')
    readonly_fields = ('entity_id', 'created_by', 'updated_by', 'institution')
    list_display = ('name_english', 'entity_id', admin_list_linkify('institution', 'name'))


badgr_admin.register(Institution, InstitutionAdmin)
badgr_admin.register(Faculty, FacultyAdmin)
