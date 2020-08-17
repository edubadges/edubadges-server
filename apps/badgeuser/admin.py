from django.contrib.admin import ModelAdmin, TabularInline
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
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


class TermsInlineForm(ModelForm):
    class Meta:
        model = Terms
        fields = ('terms_type', 'version', 'entity_id')

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        # add a default rating if one hasn't been passed in
        initial['terms_type'] = initial.get('terms_type', None)
        initial['version'] = initial.get('version', 1)
        kwargs['initial'] = initial
        super(TermsInlineForm, self).__init__(
            *args, **kwargs
        )


class TermsInline(TabularInline):
    model = Terms
    extra = 0

    form = TermsInlineForm
    readonly_fields = ('entity_id',)


class TermsUrlInline(TabularInline):
    model = TermsUrl
    extra = 0


class TermsAdmin(ModelAdmin):
    list_display = ('institution', 'terms_type', 'version', 'created_at', 'terms_url_count')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by', 'entity_id')

    inlines = [TermsUrlInline]

    def terms_url_count(self, obj):
        return len(obj.terms_urls.all())


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

    def get_form(self, request, obj=None, **kwargs):
        form = super(UserProvisionmentAdmin, self).get_form(request, obj, **kwargs)
        content_type = ContentType.objects.get(model='institution')
        form.base_fields['content_type'].initial = content_type.id
        form.base_fields['content_type'].disabled = True
        form.base_fields['content_type'].help_text = "This field is not editable"
        form.base_fields['object_id'].help_text = "Set the ID of the institution the invite is for"
        return form


badgr_admin.register(UserProvisionment, UserProvisionmentAdmin)
