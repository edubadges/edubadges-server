from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import Group

from externaltools.models import ExternalToolUserActivation
from mainsite.admin import badgr_admin, FilterByScopeMixin
from .models import BadgeUser, EmailAddressVariant, TermsVersion, TermsAgreement, \
    CachedEmailAddress, BadgeUserProxy, GroupEntity


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


class EmailAddressInline(TabularInline):
    model = CachedEmailAddress
    fk_name = 'user'
    extra = 0
    fields = ('email','verified','primary')


class BadgeUserAdmin(FilterByScopeMixin, UserAdmin):
    
    actions = None
    readonly_fields = ('email', 'first_name', 'last_name', 'entity_id', 'date_joined', 'last_login', 'username', 'entity_id', 'agreed_terms_version')
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'faculties')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'entity_id')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'password')}),
        ('Permissions', {'fields': ('groups',)}),
        ('Faculties', {'fields': ('faculty',) }),
    )
    filter_horizontal = ('faculty','groups', 'user_permissions')

    def filter_queryset_institution(self, queryset, request):
        institution_id = request.user.institution.id
        return queryset.filter(institution_id=institution_id).distinct()

    def filter_queryset_faculty(self, queryset, request):
        return queryset.filter(faculty__in=request.user.faculty.all()).distinct()

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        '''
        Overrides super.formfield_for_manytomany to filter:
            1) the faculty list according to user scope
            2) the group list according to group membership
        '''
        form_field = super(BadgeUserAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
        if db_field.attname == 'faculty':
            if not request.user.is_superuser:
                if request.user.has_perm('badgeuser.has_institution_scope'):
                    institution_id = request.user.institution.id
                    form_field.queryset = form_field.queryset.filter(institution_id=institution_id)
                elif request.user.has_perm('badgeuser.has_faculty_scope'):
                    list_of_faculty_ids = request.user.faculty.all().values_list('id')
                    form_field.queryset = form_field.queryset.filter(id__in=list_of_faculty_ids)
                else:
                    form_field.queryset = form_field.queryset.none()

        elif db_field.attname == 'groups':
            if not request.user.is_superuser:
                form_field.queryset = form_field.queryset.exclude(name='Superuser')
                if not request.user.has_perm('badgeuser.has_institution_scope'):
                    form_field.queryset = form_field.queryset.exclude(name='Instellings Admin')
                    if not request.user.has_perm('badgeuser.has_faculty_scope'):
                        form_field.queryset = form_field.queryset.exclude(name='Faculteits Admin')
        return form_field
     
    def faculties(self, obj):
        return [f.name for f in obj.faculty.all()]

badgr_admin.register(BadgeUser, BadgeUserAdmin)


class BadgeUserProxyAdmin(BadgeUserAdmin):
    actions = UserAdmin.actions
    readonly_fields = ('entity_id', 'date_joined', 'last_login', 'username', 'entity_id', 'agreed_terms_version')
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'entity_id', 'date_joined', 'faculties')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name', 'badgrapp', 'agreed_terms_version', 'marketing_opt_in')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'is_superuser', 'password')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
        ('Faculties', {'fields': ('faculty',) }),
    )
    inlines = [
        EmailAddressInline,
        ExternalToolInline,
        TermsAgreementInline,
    ]

    def faculties(self, obj):
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
            'latest_terms_version', 'is_active','version','teacher','short_description',
        )})
    )

    def latest_terms_version(self, obj):
        return TermsVersion.cached.latest_version()

    latest_terms_version.short_description = "Current Terms Version"

badgr_admin.register(TermsVersion, TermsVersionAdmin)


# class GroupAdmin(GroupAdmin):
#     model = Group
#     fields = ('name', 'permissions')

# badgr_admin.unregister(Group)
# badgr_admin.register(Group, GroupAdmin)


badgr_admin.register(GroupEntity)

