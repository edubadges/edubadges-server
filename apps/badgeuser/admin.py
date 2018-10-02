from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.auth.admin import UserAdmin

from externaltools.models import ExternalToolUserActivation
from mainsite.admin import badgr_admin

from .models import BadgeUser, BadgeUserProxy, EmailAddressVariant, TermsVersion, TermsAgreement
from . import utils


class ExternalToolInline(TabularInline):
    model = ExternalToolUserActivation
    fk_name = 'user'
    fields = ('externaltool',)
    extra = 0


class TermsAgreementInline(TabularInline):
    model = TermsAgreement
    fk_name = 'user'
    extra = 0
    max_num = 0
    can_delete = False
    readonly_fields = ('created_at', 'terms_version')
    fields = ('created_at', 'terms_version')


# class AdminQuerysetFilterMixin(object):
#
# #     def _object_in_scope(self, request, object_id):
# #         if not request.user.is_superuser:
# #             if request.user.has_perm(u'badgeuser.has_institution_scope'):
# #
# #             elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
#
#     def get_queryset(self, request):
#         """
#         Abstract class to handle queryset filtering in Admin pages
#         """
#         qs = self.model._default_manager.get_queryset()
#         if not request.user.is_superuser:
#             if request.user.has_perm(u'badgeuser.has_institution_scope'):
#                 institution_id = request.user.faculty.first().institution.id
#                 qs = qs.filter(faculty__institution_id=institution_id).distinct()
#             elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
#                 qs = qs.filter(faculty__in=request.user.faculty.all()).distinct()
#         ordering = self.get_ordering(request)
#         if ordering:
#             qs = qs.order_by(*ordering)
#         return qs

#     TODO: add scope to lti admin page and make duplications modular

class BadgeUserAdmin(UserAdmin):
    actions = None
    readonly_fields = ('email', 'first_name', 'last_name', 'entity_id', 'date_joined', 'last_login', 'username', 'entity_id', 'agreed_terms_version')
    list_display = ('is_active', 'is_staff', 'entity_id', 'date_joined') #, 'get_faculties')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'entity_id')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name')}),
        ('Access', {'fields': ('is_active', 'is_staff')}),
        ('Permissions', {'fields': ('groups',)}),
        ('Faculties', {'fields': ('faculty',) }),
    )
    filter_horizontal = ('faculty','groups', 'user_permissions')
#     inlines = [
#         ExternalToolInline,
#         TermsAgreementInline
#     ]


    def get_queryset(self, request):
        """
        Override filtering in Admin page
        """
        qs = self.model._default_manager.get_queryset()
        if not request.user.is_superuser:
            if request.user.has_perm(u'badgeuser.has_institution_scope'):
                institution_id = request.user.faculty.first().institution.id
                qs = qs.filter(faculty__institution_id=institution_id).distinct()
            elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
                qs = qs.filter(faculty__in=request.user.faculty.all()).distinct()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


    def formfield_for_manytomany(self, db_field, request, **kwargs):
        '''
        Overrides super.formfield_for_manytomany to filter:
            1) the faculty list according to user scope
            2) the group list according to group membership
        '''
        form_field = super(BadgeUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.attname == 'faculty':
            if not request.user.is_superuser:
                if request.user.has_perm(u'badgeuser.has_institution_scope'):
                    institution_id = request.user.faculty.first().institution.id
                    form_field.queryset = form_field.queryset.filter(institution_id=institution_id)
                elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
                    list_of_faculty_ids = request.user.faculty.all().values_list('id')
                    form_field.queryset = form_field.queryset.filter(id__in=list_of_faculty_ids)

        elif db_field.attname == 'groups':
            if not request.user.is_superuser:
                if not request.user.has_perm(u'badgeuser.has_institution_scope'):
                  form_field.queryset = form_field.queryset.exclude(name='Instellings Admin')
        return form_field

    def change_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.change_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:badgeuser_badgeuser_changelist'))
#         self.filter_horizontal =
        return super(BadgeUserAdmin, self).change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.delete_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:badgeuser_badgeuser_changelist'))
        return super(BadgeUserAdmin, self).delete_view(request, object_id, form_url, extra_context)

    def history_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.history_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:badgeuser_badgeuser_changelist'))
        return super(BadgeUserAdmin, self).history_view(request, object_id, form_url, extra_context)



badgr_admin.register(BadgeUser, BadgeUserAdmin)


class BadgeUserProxyAdmin(BadgeUserAdmin):
    actions = ['delete_selected']
    readonly_fields = ('entity_id', 'date_joined', 'last_login', 'username', 'entity_id', 'agreed_terms_version')
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'entity_id', 'date_joined', 'get_faculties')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name', 'badgrapp', 'agreed_terms_version', 'marketing_opt_in')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'is_superuser', 'password')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Faculties', {'fields': ('faculty',) }),
    )

    def get_faculties(self, obj):
        return [f.name for f in obj.faculty.all()]

badgr_admin.register(BadgeUserProxy, BadgeUserProxyAdmin)



class EmailAddressVariantAdmin(ModelAdmin):
    search_fields = ('canonical_email', 'email',)
    list_display = ('email', 'canonical_email',)
    raw_id_fields = ('canonical_email',)

badgr_admin.register(EmailAddressVariant, EmailAddressVariantAdmin)


class TermsVersionAdmin(ModelAdmin):
    list_display = ('version','created_at','is_active')
    readonly_fields = ('created_at','created_by','updated_at','updated_by', 'latest_terms_version')
    fieldsets = (
        ('Metadata', {
            'fields': ('created_at','created_by','updated_at','updated_by'),
            'classes': ('collapse',)
        }),
        (None, {'fields': (
            'latest_terms_version', 'is_active','version','short_description',
        )})
    )

    def latest_terms_version(self, obj):
        return TermsVersion.cached.latest_version()
    latest_terms_version.short_description = "Current Terms Version"

badgr_admin.register(TermsVersion, TermsVersionAdmin)
