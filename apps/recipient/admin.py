# Created by wiggins@concentricsky.com on 5/11/16.
import basic_models
from django.contrib.admin import ModelAdmin, TabularInline
from mainsite.admin import badgr_admin
from recipient.models import RecipientGroup, RecipientProfile, RecipientGroupMembership


class RecipientGroupMembershipInline(TabularInline):
    model = RecipientGroupMembership
    extra = 0


class RecipientGroupAdmin(ModelAdmin):
    list_display = ('name', 'issuer', 'is_active', 'created_at', 'entity_id')
    list_filter = ('is_active', 'created_at',)
    search_fields = ('name', 'issuer__name')
    # readonly_fields = ('created_by','created_at','updated_by','updated_by',)
    raw_id_fields = ('issuer',)
    readonly_fields = ('entity_id',)
    filter_horizontal = ('pathways',)
    fieldsets = (
        # ('Metadata', {
        #     'fields': ('is_active','created_by','created_at','updated_by','updated_by',),
        #     'classes': ('collapse',)
        # }),
        (None, {
            'fields': ('name', 'entity_id', 'description', 'issuer', 'pathways')
        }),
    )
    inlines = [RecipientGroupMembershipInline]

badgr_admin.register(RecipientGroup, RecipientGroupAdmin)


class RecipientProfileAdmin(ModelAdmin):
    list_display = ( 'public', 'recipient_identifier', 'display_name', 'entity_id')
    search_fields = ('recipient_identifier', 'display_name',)
    # readonly_fields = ('created_by','created_at','updated_by','updated_by',)
    raw_id_fields = ('badge_user',)
    readonly_fields = ('entity_id',)
    fieldsets = (
        # ('Metadata', {
        #     'fields': ('is_active','created_by','created_at','updated_by','updated_by',),
        #     'classes': ('collapse',)
        # }),
        (None, {
            'fields': ('public','recipient_identifier', 'display_name', 'entity_id', 'badge_user',)
        }),
    )
    inlines = [RecipientGroupMembershipInline]

badgr_admin.register(RecipientProfile, RecipientProfileAdmin)
