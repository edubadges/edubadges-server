from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.auth.admin import UserAdmin
from django.forms import ModelForm
from mainsite.admin import badgr_admin
from staff.models import PermissionedRelationshipBase
from .models import BadgeUser, EmailAddressVariant, Terms, CachedEmailAddress, UserProvisionment, TermsUrl


class EmailAddressInline(TabularInline):
    model = CachedEmailAddress
    fk_name = 'user'
    extra = 0
    fields = ('email', 'verified', 'primary')


class BadgeUserAdmin(UserAdmin):
    readonly_fields = ('email', 'first_name', 'last_name', 'entity_id', 'date_joined', 'last_login', 'username', 'entity_id')
    list_display = ('email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined', 'institution')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'entity_id')
    fieldsets = (
        ('Metadata', {'fields': ('entity_id', 'username', 'date_joined',), 'classes': ('collapse',)}),
        (None, {'fields': ('email', 'first_name', 'last_name')}),
        ('Access', {'fields': ('is_active', 'is_staff', 'password')}),
        ('Permissions', {'fields': ('groups',)}),
    )
    filter_horizontal = ('groups', 'user_permissions', 'faculty',)
    inlines = [
        EmailAddressInline,
    ]

badgr_admin.register(BadgeUser, BadgeUserAdmin)

class EmailAddressVariantAdmin(ModelAdmin):
    search_fields = ('canonical_email', 'email',)
    list_display = ('email', 'canonical_email',)
    raw_id_fields = ('canonical_email',)

badgr_admin.register(EmailAddressVariant, EmailAddressVariantAdmin)



class TermsUrlInline(TabularInline):
    model = TermsUrl
    extra = 0


class TermsAdmin(ModelAdmin):
    list_display = ('institution', 'terms_type', 'version', 'created_at')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'entity_id')

    inlines = [TermsUrlInline]

badgr_admin.register(Terms, TermsAdmin)


class TermsUrlAdmin(ModelAdmin):
    list_display = ('language', 'terms')

badgr_admin.register(TermsUrl, TermsUrlAdmin)


class UserProvisionmentCreateForm(ModelForm):

    class Meta:
        model = UserProvisionment
        fields = ('email', 'object_id', 'content_type')


class UserProvisionmentAdmin(ModelAdmin):
    form = UserProvisionmentCreateForm
    list_display = ('created_at', 'email', 'type', 'rejected')
    add_form_template = 'admin/custom/userprovisionment_add_form.html'

    def save_model(self, request, obj, form, change):
        obj.created_by = request.user
        obj.data = PermissionedRelationshipBase.full_permissions()
        obj.for_teacher = True
        obj.type = obj.TYPE_FIRST_ADMIN_INVITATION
        obj.save()


badgr_admin.register(UserProvisionment, UserProvisionmentAdmin)
