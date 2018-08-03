from django.contrib.admin import ModelAdmin, TabularInline

from django.contrib.auth.admin import UserAdmin


from externaltools.models import ExternalToolUserActivation
from mainsite.admin import badgr_admin

from .models import BadgeUser, EmailAddressVariant, TermsVersion, TermsAgreement


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

class BadgeUserAdmin(UserAdmin):
    readonly_fields = ('entity_id', 'date_joined', 'last_login', 'username', 'entity_id', 'agreed_terms_version')
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'entity_id', 'date_joined', 'user_type')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'entity_id')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name', 'badgrapp', 'agreed_terms_version', 'marketing_opt_in')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'is_superuser', 'password')}),
        ('Permissions', {'fields': ('groups', 'user_permissions')}),
    )
    inlines = [
        ExternalToolInline,
        TermsAgreementInline
    ]
    
    def set_user_to_non_issuer(self, request, queryset):
        queryset.update(user_type=1)
    set_user_to_non_issuer.short_description = 'Set user(s) to Non Issuer'

    def set_user_to_issuer(self, request, queryset):
        queryset.update(user_type=2)
    set_user_to_issuer.short_description = 'Set user(s) to Issuer'

    def set_user_to_issuer_admin(self, request, queryset):
            queryset.update(user_type=3)
    set_user_to_issuer_admin.short_description = 'Set user(s) to Issuer Admin'


    actions = [set_user_to_non_issuer, set_user_to_issuer, set_user_to_issuer_admin]
    

badgr_admin.register(BadgeUser, BadgeUserAdmin)

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
