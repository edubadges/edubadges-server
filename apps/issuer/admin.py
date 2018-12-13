from __future__ import unicode_literals

from django.contrib.admin import ModelAdmin, StackedInline, TabularInline
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from django_object_actions import DjangoObjectActions

from mainsite.admin import badgr_admin, FilterByScopeMixin

from .models import Issuer, BadgeClass, BadgeInstance, BadgeInstanceEvidence, BadgeClassAlignment, BadgeClassTag, \
    BadgeClassExtension, IssuerExtension, BadgeInstanceExtension


class IssuerStaffInline(TabularInline):
    model = Issuer.staff.through
    extra = 0
    raw_id_fields = ('user',)


class IssuerExtensionInline(TabularInline):
    model = IssuerExtension
    extra = 0
    fields = ('name', 'original_json')


class IssuerAdmin(DjangoObjectActions, FilterByScopeMixin, ModelAdmin):
    
    def filter_queryset_institution(self, queryset, request):
        institution_id = request.user.institution.id
        return queryset.filter(faculty__institution_id=institution_id).distinct()
    
    def filter_queryset_faculty(self, queryset, request):
        return queryset.filter(faculty__in=request.user.faculty.all()).distinct()
    
    readonly_fields = ('created_at', 'created_by', 'old_json', 'source', 'source_url', 'entity_id', 'slug')
    list_display = ('img', 'name', 'entity_id', 'created_by', 'created_at', 'faculty')
    list_display_links = ('img', 'name')
    list_filter = ('created_at',)
    search_fields = ('name', 'entity_id')
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'source', 'source_url', 'entity_id', 'slug'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('image', 'name', 'url', 'email', 'description', 'badgrapp')
        }),
        ('JSON', {
            'fields': ('old_json',)
        }),
        ('Faculties', {
            'fields': ('faculty',) 
        }),
    )
    inlines = [
        IssuerStaffInline,
        IssuerExtensionInline
    ]
    change_actions = ['redirect_badgeclasses']

    def img(self, obj):
        try:
            return u'<img src="{}" width="32"/>'.format(obj.image.url)
        except ValueError:
            return obj.image
    img.short_description = 'Image'
    img.allow_tags = True

    def redirect_badgeclasses(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:issuer_badgeclass_changelist') + '?issuer__id={}'.format(obj.id)
        )
    redirect_badgeclasses.label = "BadgeClasses"
    redirect_badgeclasses.short_description = "See this issuer's defined BadgeClasses"

badgr_admin.register(Issuer, IssuerAdmin)


class BadgeClassAlignmentInline(TabularInline):
    model = BadgeClassAlignment
    extra = 0
    fields = ('target_name','target_url','target_description', 'target_framework','target_code')


class BadgeClassTagInline(TabularInline):
    model = BadgeClassTag
    extra = 0
    fields = ('name',)


class BadgeClassExtensionInline(TabularInline):
    model = BadgeClassExtension
    extra = 0
    fields = ('name', 'original_json')


class BadgeClassAdmin(DjangoObjectActions, ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'old_json', 'source', 'source_url', 'entity_id', 'slug')
    list_display = ('badge_image', 'name', 'entity_id', 'issuer_link', 'recipient_count')
    list_display_links = ('badge_image', 'name',)
    list_filter = ('created_at',)
    search_fields = ('name', 'entity_id', 'issuer__name',)
    raw_id_fields = ('issuer',)
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'source', 'source_url', 'entity_id', 'slug'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('issuer', 'image', 'name', 'description')
        }),
        ('Criteria', {
            'fields': ('criteria_url', 'criteria_text',)
        }),
        ('JSON', {
            'fields': ('old_json',)
        }),
    )
    inlines = [
        BadgeClassTagInline,
        BadgeClassAlignmentInline,
        BadgeClassExtensionInline,
    ]
    change_actions = ['redirect_issuer', 'redirect_instances', 'redirect_pathwaybadges']

    def badge_image(self, obj):
        return u'<img src="{}" width="32"/>'.format(obj.image.url) if obj.image else ''
    badge_image.short_description = 'Badge'
    badge_image.allow_tags = True

    def issuer_link(self, obj):
        return '<a href="{}">{}</a>'.format(reverse("admin:issuer_issuer_change", args=(obj.issuer.id,)), obj.issuer.name)
    issuer_link.allow_tags=True

    def redirect_instances(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:issuer_badgeinstance_changelist') + '?badgeclass__id={}'.format(obj.id)
        )
    redirect_instances.label = "Instances"
    redirect_instances.short_description = "See awarded instances of this BadgeClass"

    def redirect_issuer(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:issuer_issuer_change', args=(obj.issuer.id,))
        )
    redirect_issuer.label = "Issuer"
    redirect_issuer.short_description = "See this Issuer"

    def redirect_pathwaybadges(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:pathway_pathwayelementbadge_changelist') + '?badgeclass__id={}'.format(obj.id)
        )
    redirect_pathwaybadges.label = "Pathway Badges"
    redirect_pathwaybadges.short_description = "Pathway Badges"

badgr_admin.register(BadgeClass, BadgeClassAdmin)


class BadgeEvidenceInline(StackedInline):
    model = BadgeInstanceEvidence
    fields = ('evidence_url', 'narrative',)
    extra = 0


class BadgeInstanceExtensionInline(TabularInline):
    model = BadgeInstanceExtension
    extra = 0
    fields = ('name', 'original_json')


class BadgeInstanceAdmin(DjangoObjectActions, ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'updated_at','updated_by', 'image', 'entity_id', 'old_json', 'salt', 'entity_id', 'slug', 'source', 'source_url')
    list_display = ('badge_image', 'recipient_identifier', 'entity_id', 'badgeclass', 'issuer')
    list_display_links = ('badge_image', 'recipient_identifier', )
    list_filter = ('created_at',)
    search_fields = ('recipient_identifier', 'entity_id', 'badgeclass__name', 'issuer__name')
    raw_id_fields = ('badgeclass', 'issuer')
    fieldsets = (
        ('Metadata', {
            'fields': ('source', 'source_url', 'created_by', 'created_at', 'updated_by','updated_at', 'entity_id', 'slug', 'salt'),
            'classes': ("collapse",)
        }),
        ('Badgeclass', {
            'fields': ('badgeclass', 'issuer')
        }),
        ('Assertion', {
            'fields': ('entity_id', 'acceptance', 'recipient_type', 'recipient_identifier', 'image', 'issued_on', 'expires_at', 'narrative')
        }),
        ('Revocation', {
            'fields': ('revoked', 'revocation_reason')
        }),
        ('JSON', {
            'fields': ('old_json',)
        }),
    )
    actions = ['rebake']
    change_actions = ['redirect_issuer', 'redirect_badgeclass']
    inlines = [
        BadgeEvidenceInline,
        BadgeInstanceExtensionInline
    ]

    def rebake(self, request, queryset):
        for obj in queryset:
            obj.rebake(save=True)
    rebake.short_description = "Rebake selected badge instances"

    def badge_image(self, obj):
        try:
            return u'<img src="{}" width="32"/>'.format(obj.image.url)
        except ValueError:
            return obj.image
    badge_image.short_description = 'Badge'
    badge_image.allow_tags = True

    def has_add_permission(self, request):
        return False

    def redirect_badgeclass(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:issuer_badgeclass_change', args=(obj.badgeclass.id,))
        )
    redirect_badgeclass.label = "BadgeClass"
    redirect_badgeclass.short_description = "See this BadgeClass"

    def redirect_issuer(self, request, obj):
        return HttpResponseRedirect(
            reverse('admin:issuer_issuer_change', args=(obj.issuer.id,))
        )
    redirect_issuer.label = "Issuer"
    redirect_issuer.short_description = "See this Issuer"

badgr_admin.register(BadgeInstance, BadgeInstanceAdmin)


class ExtensionAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'original_json')

badgr_admin.register(IssuerExtension, ExtensionAdmin)
badgr_admin.register(BadgeClassExtension, ExtensionAdmin)
badgr_admin.register(BadgeInstanceExtension, ExtensionAdmin)
