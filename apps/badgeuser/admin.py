from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.auth.admin import UserAdmin
from mainsite.admin import badgr_admin, FilterByScopeMixin
from .models import BadgeUser, EmailAddressVariant, TermsVersion, TermsAgreement, \
    CachedEmailAddress, BadgeUserProxy, GroupEntity


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
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'institution')
    list_filter = ('is_active', 'is_staff', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'entity_id')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'password')}),
        ('Permissions', {'fields': ('groups',)}),
        # ('Faculties', {'fields': ('faculty',) }),
    )
    filter_horizontal = ( 'groups', 'user_permissions')

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
        # ('Permissions', {'fields': ('groups', 'user_permissions')}),
        # ('Faculties', {'fields': ('faculties',) }),
    )
    filter_horizontal = ('faculty',)
    inlines = [
        EmailAddressInline,
        # ExternalToolInline,
        TermsAgreementInline,
    ]

    def faculties(self, obj):
        return [f.name for f in obj.faculty_set.all()]

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


badgr_admin.register(GroupEntity)

