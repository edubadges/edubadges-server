# Created by wiggins@concentricsky.com on 10/8/15.
import basic_models
from allauth.socialaccount.models import SocialToken, SocialAccount

from django.contrib.admin import AdminSite, ModelAdmin, StackedInline
from django.utils.module_loading import autodiscover_modules
from django.utils.translation import ugettext_lazy
from oauth2_provider.models import get_application_model, get_grant_model, get_access_token_model, \
    get_refresh_token_model

from badgeuser.models import CachedEmailAddress, ProxyEmailConfirmation
from mainsite.admin_actions import delete_selected
from mainsite.models import BadgrApp, EmailBlacklist, ApplicationInfo
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

class BadgrAdminSite(AdminSite):
    site_header = ugettext_lazy('Badgr')
    index_title = ugettext_lazy('Staff Dashboard')
    site_title = 'Badgr'

    def autodiscover(self):
        autodiscover_modules('admin', register_to=self)


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
            'fields': ('name', 'cors', 'oauth_authorization_redirect'),
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

from rest_framework.authtoken.models import Token
class TokenAdmin(ModelAdmin):
    list_display = ('key','user','created')
    list_filter = ('created',)
    raw_id_fields = ('user',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
badgr_admin.register(Token, TokenAdmin)

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

from oauth2_provider.admin import ApplicationAdmin, GrantAdmin, AccessTokenAdmin, RefreshTokenAdmin

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
badgr_admin.register(Grant, GrantAdmin)
badgr_admin.register(AccessToken, AccessTokenAdmin)
badgr_admin.register(RefreshToken, RefreshTokenAdmin)


class FilterByScopeMixin(object):
    
    def get_queryset(self, request):
        """
        Override filtering in Admin page
        """
        qs = self.model._default_manager.get_queryset()
        if not request.user.is_superuser:
            if request.user.has_perm(u'badgeuser.has_institution_scope'):
                institution_id = request.user.faculty.first().institution.id
                qs = qs.filter(faculty__institution_id=institution_id).distinct()
            elif request.user.has_perm(u'badgeuser.has_faculty_scope'):
                qs = qs.filter(faculty__in=request.user.faculty.all()).distinct()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.change_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:{}_{}_changelist'.format(self.model._meta.app_label, self.model._meta.model_name)))
        return super(FilterByScopeMixin, self).change_view(request, object_id, form_url, extra_context)

    def delete_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.delete_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:{}_{}_changelist'.format(self.model._meta.app_label, self.model._meta.model_name)))
        return super(FilterByScopeMixin, self).delete_view(request, object_id, extra_context)

    def history_view(self, request, object_id, form_url='', extra_context=None):
        '''
        Overrides super.history_view to add a check to see if this object is in the request.user's scope
        '''
        if not self.get_queryset(request).filter(id=object_id).exists():
            return HttpResponseRedirect(reverse('admin:{}_{}_changelist'.format(self.model._meta.app_label, self.model._meta.model_name)))
        return super(FilterByScopeMixin, self).history_view(request, object_id, extra_context)


