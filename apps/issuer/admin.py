from __future__ import unicode_literals

from django.contrib.admin import ModelAdmin, TabularInline
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from django_object_actions import DjangoObjectActions

from mainsite.admin import badgr_admin

from .models import Issuer, BadgeClass, BadgeInstance, BadgeInstanceEvidence


class IssuerAdmin(DjangoObjectActions, ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'old_json', 'source', 'source_url')
    list_display = ('img', 'name', 'slug', 'created_by', 'created_at')
    list_display_links = ('img', 'name')
    list_filter = ('created_at',)
    search_fields = ('name', 'slug')
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'source', 'source_url', 'slug', 'entity_id'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('image', 'name', 'url', 'email', 'description')
        }),
        # ('JSON', {
        #     'fields': ('old_json',)
        # }),
    )
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


class BadgeClassAdmin(DjangoObjectActions, ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'old_json', 'source', 'source_url')
    list_display = ('badge_image', 'name', 'slug', 'issuer_link', 'recipient_count')
    list_display_links = ('badge_image', 'name',)
    list_filter = ('created_at',)
    search_fields = ('name', 'slug', 'issuer__name',)
    raw_id_fields = ('issuer',)
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'source', 'source_url', 'slug'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('issuer', 'image', 'name', 'description')
        }),
        ('Criteria', {
            'fields': ('criteria_url', 'criteria_text',)
        }),
        # ('JSON', {
        #     'fields': ('old_json',)
        # }),
    )
    change_actions = ['redirect_issuer', 'redirect_instances']

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

badgr_admin.register(BadgeClass, BadgeClassAdmin)


class BadgeEvidenceInline(TabularInline):
    model = BadgeInstanceEvidence
    fields = ('evidence_url','narrative',)
    extra = 0


class BadgeInstanceAdmin(DjangoObjectActions, ModelAdmin):
    readonly_fields = ('created_at', 'created_by', 'image', 'slug', 'old_json')
    list_display = ('badge_image', 'recipient_identifier', 'slug', 'badgeclass', 'issuer')
    list_display_links = ('badge_image', 'recipient_identifier', )
    list_filter = ('created_at',)
    search_fields = ('recipient_identifier', 'slug', 'badgeclass__name', 'issuer__name')
    raw_id_fields = ('badgeclass', 'issuer')
    fieldsets = (
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'slug', 'salt', 'badgeclass', 'issuer'),
            'classes': ("collapse",)
        }),
        (None, {
            'fields': ('acceptance', 'recipient_identifier', 'image')
        }),
        ('Revocation', {
            'fields': ('revoked', 'revocation_reason')
        }),
        # ('JSON', {
        #     'fields': ('old_json',)
        # }),
    )
    change_actions = ['redirect_issuer', 'redirect_badgeclass']
    inlines = (BadgeEvidenceInline,)

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
