# Created by wiggins@concentricsky.com on 10/8/15.
import basic_models
from allauth.socialaccount.models import SocialToken, SocialAccount

from django.contrib.admin import AdminSite, ModelAdmin
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import ugettext_lazy

from badgeuser.models import CachedEmailAddress, ProxyEmailConfirmation
from mainsite.admin_actions import delete_selected
from mainsite.models import BadgrApp, EmailBlacklist


class BadgrAdminSite(AdminSite):
    site_header = ugettext_lazy('Badgr')
    index_title = ugettext_lazy('Staff Dashboard')
    site_title = 'Badgr'

    def autodiscover(self):
        autodiscover_modules('admin', register_to=self)


badgr_admin = BadgrAdminSite(name='badgradmin')

# patch in our delete_selected that calls obj.delete()
badgr_admin.disable_action('delete_selected')
badgr_admin.add_action(delete_selected)


class BadgrAppAdmin(basic_models.DefaultModelAdmin):
    fieldsets = (
        ('Meta', {'fields': ('is_active', 'created_at', 'created_by', 'updated_at', 'updated_by'),
                  'classes': ('collapse',)}),
        (None, {'fields': ('name', 'cors', 'signup_redirect', 'email_confirmation_redirect', 'forgot_password_redirect', 'ui_login_redirect', 'ui_signup_success_redirect', 'ui_connect_success_redirect')})
    )
    list_display = ('name', 'cors',)
badgr_admin.register(BadgrApp, BadgrAppAdmin)


class EmailBlacklistAdmin(ModelAdmin):
    readonly_fields = ('email',)
    list_display = ('email',)
    search_fields = ('email',)
badgr_admin.register(EmailBlacklist, EmailBlacklistAdmin)

# 3rd party apps

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
