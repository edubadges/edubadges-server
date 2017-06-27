# Created by wiggins@concentricsky.com on 5/11/16.
import basic_models
from django.contrib.admin import ModelAdmin, TabularInline
from mainsite.admin import badgr_admin
from recipient.models import RecipientGroup, RecipientProfile, RecipientGroupMembership


class RecipientGroupMembershipInline(TabularInline):
    model = RecipientGroupMembership
    extra = 0
    raw_id_fields = ('recipient_profile',)
    exclude = ('slug', 'entity_version',)
    readonly_fields = ('entity_id',)


class RecipientGroupAdmin(ModelAdmin):
    list_display = ('name', 'issuer', 'is_active', 'created_at', 'entity_id')
    list_filter = ('is_active', 'created_at',)
    search_fields = ('name', 'issuer__name')
    readonly_fields = ('created_by', 'created_at', 'created_by', 'entity_id', 'slug')
    raw_id_fields = ('issuer',)
    filter_horizontal = ('pathways',)
    fieldsets = (
        ('Metadata', {
            'fields': ('is_active', 'created_by', 'created_at', 'entity_id', 'slug'),
            'classes': ('collapse',)
        }),
        (None, {
            'fields': ('name', 'description', 'issuer', 'pathways')
        }),
    )
    inlines = [RecipientGroupMembershipInline]

badgr_admin.register(RecipientGroup, RecipientGroupAdmin)


class RecipientProfileAdmin(ModelAdmin):
    list_display = ( 'public', 'recipient_identifier', 'display_name', 'entity_id')
    search_fields = ('recipient_identifier', 'display_name',)
    raw_id_fields = ('badge_user',)
    readonly_fields = ('created_by', 'created_at', 'entity_id', 'slug')
    fieldsets = (
        ('Metadata', {
            'fields': ('is_active', 'created_by', 'created_at', 'entity_id', 'slug',),
            'classes': ('collapse',)
        }),
        (None, {
            'fields': ('public', 'recipient_identifier', 'display_name', 'badge_user')
        }),
    )
    inlines = [RecipientGroupMembershipInline]

badgr_admin.register(RecipientProfile, RecipientProfileAdmin)
