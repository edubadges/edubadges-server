# Created by wiggins@concentricsky.com on 10/8/15.
from allauth.socialaccount.models import SocialToken, SocialAccount
from django.contrib.admin import AdminSite, ModelAdmin, StackedInline
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import ugettext_lazy
from oauth2_provider.models import get_application_model, get_grant_model, get_access_token_model, \
    get_refresh_token_model

import badgrlog
from badgeuser.models import CachedEmailAddress, ProxyEmailConfirmation
from mainsite.models import BadgrApp, EmailBlacklist, ApplicationInfo, AccessTokenProxy, LegacyTokenProxy

badgrlogger = badgrlog.BadgrLogger()


class BadgrAdminSite(AdminSite):
    site_header = ugettext_lazy('Badgr')
    index_title = ugettext_lazy('Staff Dashboard')
    site_title = 'Badgr'

    def autodiscover(self):
        autodiscover_modules('admin', register_to=self)

    def login(self, request, extra_context=None):
        response = super(BadgrAdminSite, self).login(request, extra_context)
        if request.method == 'POST':
            # form submission
            if response.status_code != 302:
                # failed /staff login
                username = request.POST.get('username', None)
                badgrlogger.event(badgrlog.FailedLoginAttempt(request, username, endpoint='/staff/login'))

        return response


badgr_admin = BadgrAdminSite(name='badgradmin')

# patch in our delete_selected that calls obj.delete()
# FIXME: custom action broken for django 1.10+
# badgr_admin.disable_action('delete_selected')
# badgr_admin.add_action(delete_selected)


class BadgrAppAdmin(ModelAdmin):
    fieldsets = (
        ('Meta', {'fields': ('is_active', ),
                  'classes': ('collapse',)}),
        (None, {
            'fields': ('name', 'cors', 'oauth_authorization_redirect', 'use_auth_code_exchange'),
        }),
        ('signup', {
            'fields': ('signup_redirect', 'email_confirmation_redirect', 'forgot_password_redirect', 'ui_login_redirect', 'ui_signup_success_redirect', 'ui_connect_success_redirect')
        }),
        ('public', {
            'fields': ('public_pages_redirect',)
        })
    )
    list_display = ('name', 'cors',)
badgr_admin.register(BadgrApp, BadgrAppAdmin)


class EmailBlacklistAdmin(ModelAdmin):
    readonly_fields = ('email',)
    list_display = ('email',)
    search_fields = ('email',)
badgr_admin.register(EmailBlacklist, EmailBlacklistAdmin)

# 3rd party apps

class LegacyTokenAdmin(ModelAdmin):
    list_display = ('obscured_token','user','created')
    list_filter = ('created',)
    raw_id_fields = ('user',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('obscured_token','created')
    fields = ('obscured_token', 'user', 'created')

badgr_admin.register(LegacyTokenProxy, LegacyTokenAdmin)

from allauth.account.admin import EmailAddressAdmin, EmailConfirmationAdmin
from allauth.socialaccount.admin import SocialApp, SocialAppAdmin, SocialTokenAdmin, SocialAccountAdmin
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

badgr_admin.register(SocialApp, SocialAppAdmin)
badgr_admin.register(SocialToken, SocialTokenAdmin)
badgr_admin.register(SocialAccount, SocialAccountAdmin)

badgr_admin.register(Site, SiteAdmin)
badgr_admin.register(Group, GroupAdmin)

badgr_admin.register(CachedEmailAddress, EmailAddressAdmin)
badgr_admin.register(ProxyEmailConfirmation, EmailConfirmationAdmin)

from oauth2_provider.admin import ApplicationAdmin, AccessTokenAdmin

Application = get_application_model()
Grant = get_grant_model()
AccessToken = get_access_token_model()
RefreshToken = get_refresh_token_model()


class ApplicationInfoInline(StackedInline):
    model = ApplicationInfo
    extra = 1


class ApplicationInfoAdmin(ApplicationAdmin):
    inlines = [
        ApplicationInfoInline
    ]
badgr_admin.register(Application, ApplicationInfoAdmin)
# badgr_admin.register(Grant, GrantAdmin)
# badgr_admin.register(RefreshToken, RefreshTokenAdmin)


class SecuredAccessTokenAdmin(AccessTokenAdmin):
    list_display = ("obscured_token", "user", "application", "expires")
    raw_id_fields = ('user','application')
    fields = ('obscured_token','user','application','expires','scope',)
    readonly_fields = ('obscured_token',)
badgr_admin.register(AccessTokenProxy, SecuredAccessTokenAdmin)

