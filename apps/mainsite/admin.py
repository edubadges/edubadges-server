# Created by wiggins@concentricsky.com on 10/8/15.
import basic_models

from django.contrib.admin import AdminSite
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import ugettext_lazy
from mainsite.admin_actions import delete_selected


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



# 3rd party apps

from allauth.account.admin import EmailAddressAdmin, EmailConfirmationAdmin
from allauth.account.models import EmailAddress, EmailConfirmation
from django.contrib.auth.admin import GroupAdmin
from django.contrib.auth.models import Group
from django.contrib.sites.admin import SiteAdmin
from django.contrib.sites.models import Site

badgr_admin.register(Site, SiteAdmin)
badgr_admin.register(Group, GroupAdmin)

badgr_admin.register(EmailAddress, EmailAddressAdmin)
badgr_admin.register(EmailConfirmation, EmailConfirmationAdmin)
