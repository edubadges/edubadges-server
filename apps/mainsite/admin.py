# Created by wiggins@concentricsky.com on 10/8/15.
import badgrlog
from allauth.socialaccount.models import SocialToken, SocialAccount
from badgeuser.models import CachedEmailAddress, ProxyEmailConfirmation
from django.conf import settings
from django.utils import timezone
from django.contrib import admin
from django_otp.admin import OTPAdminSite
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django.contrib.admin import AdminSite, ModelAdmin, StackedInline
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import gettext_lazy
from mainsite.models import BadgrApp, EmailBlacklist, ApplicationInfo, AccessTokenProxy, LegacyTokenProxy, \
    SystemNotification
from oauth2_provider.models import get_application_model, get_grant_model, get_access_token_model, \
    get_refresh_token_model

badgrlogger = badgrlog.BadgrLogger()


class BadgrAdminSite(OTPAdminSite):
    site_header = gettext_lazy('Badgr')
    index_title = gettext_lazy('Staff Dashboard')
    site_title = 'Badgr'

    # login_template = 'admin/superlogin.html' if settings.SUPERUSER_LOGIN_WITH_SURFCONEXT else None

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


badgr_admin = BadgrAdminSite(OTPAdminSite.name)
# badgr_admin.register(User)
badgr_admin.register(TOTPDevice, TOTPDeviceAdmin)
admin.site.__class__ = OTPAdminSite


class BadgrAppAdmin(ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('name', 'is_demo_environment'),
        }),
    )
    list_display = ('name', 'is_demo_environment',)
    list_display_links = ('name', 'is_demo_environment',)


badgr_admin.register(BadgrApp, BadgrAppAdmin)


class EmailBlacklistAdmin(ModelAdmin):
    readonly_fields = ('email',)
    list_display = ('email',)
    search_fields = ('email',)


badgr_admin.register(EmailBlacklist, EmailBlacklistAdmin)


# 3rd party apps

class LegacyTokenAdmin(ModelAdmin):
    list_display = ('obscured_token', 'user', 'created')
    list_filter = ('created',)
    raw_id_fields = ('user',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('obscured_token', 'created')
    fields = ('obscured_token', 'user', 'created')


badgr_admin.register(LegacyTokenProxy, LegacyTokenAdmin)

from allauth.account.admin import EmailAddressAdmin, EmailConfirmationAdmin
from allauth.socialaccount.admin import SocialApp, SocialAppAdmin, SocialTokenAdmin
from badgrsocialauth.admin import BadgrSocialAccountAdmin

from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

badgr_admin.register(SocialApp, SocialAppAdmin)
badgr_admin.register(SocialToken, SocialTokenAdmin)
badgr_admin.register(SocialAccount, BadgrSocialAccountAdmin)

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


class SecuredAccessTokenAdmin(AccessTokenAdmin):
    list_display = ("obscured_token", "user", "application", "expires")
    raw_id_fields = ('user', 'application')
    fields = ('obscured_token', 'user', 'application', 'expires', 'scope',)
    readonly_fields = ('obscured_token',)


badgr_admin.register(AccessTokenProxy, SecuredAccessTokenAdmin)


class SystemNotificationAdmin(ModelAdmin):
    list_display = ('title', 'display_start', 'display_end', 'notification_type')
    fields = ('title', 'display_start', 'display_end', 'notification_en', 'notification_nl', 'notification_type',)
    search_fields = ('title', 'notification_en', 'notification_nl', 'notification_type',)

    def __init__(self, model, admin_site):
        timezone.activate("Europe/Amsterdam")
        super().__init__(model, admin_site)


badgr_admin.register(SystemNotification, SystemNotificationAdmin)
