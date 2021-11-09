import datetime
import os
import urllib.error
import urllib.parse
import urllib.parse
import urllib.request

from allauth.account.adapter import get_adapter
from allauth.account.utils import perform_login
from allauth.socialaccount import app_settings
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.base import AuthProcess
from django.contrib.auth import authenticate
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse, NoReverseMatch
from django.views.generic import RedirectView
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import BadgeUser
from badgrsocialauth.permissions import IsSuperUser
from badgrsocialauth.utils import set_url_query_params, set_session_badgr_app, get_session_badgr_app, \
    get_session_verification_email, set_session_authcode
from institution.models import Institution
from mainsite.models import BadgrApp

from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch, DjangoCacheDataStorage
from pylti1p3.grade import Grade
from pylti1p3.tool_config.abstract import ToolConfAbstract
from pylti1p3.lineitem import LineItem
from pylti1p3.tool_config import ToolConfJsonFile
from badgrsocialauth.utils import set_url_query_params, set_session_badgr_app, get_session_badgr_app, \
    get_session_verification_email, set_session_authcode
from mainsite.models import BadgrApp

from badgeuser.models import BadgeUser
from mainsite import TOP_DIR
from mainsite.models import BadgrApp


class ExtendedDjangoMessageLaunch(DjangoMessageLaunch):

    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.
        """
        iss = self.get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super(ExtendedDjangoMessageLaunch, self).validate_nonce()

# TODO - Change this with Database tool config
def get_tool_conf():
    lti_config_path = os.path.join(TOP_DIR, 'apps', 'lti13', 'config', 'lms.json')
    tool_conf = ToolConfJsonFile(lti_config_path)
    return tool_conf


def get_launch_data_storage():
    return DjangoCacheDataStorage()


def get_launch_url(request):
    target_link_uri = request.POST.get('target_link_uri', request.GET.get('target_link_uri'))
    if not target_link_uri:
        raise Exception('Missing "target_link_uri" param')
    return target_link_uri


def login(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()

    oidc_login = DjangoOIDCLogin(request, tool_conf, launch_data_storage=launch_data_storage)
    target_link_uri = get_launch_url(request)
    oidc_redirect = oidc_login.enable_check_cookies().redirect(target_link_uri)
    return oidc_redirect


@require_POST
def launch(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = ExtendedDjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage)
    message_launch_data = message_launch.get_launch_data()

    if not message_launch.has_nrps():
        return HttpResponseForbidden("Don't have names and roles!")

    if not message_launch.has_ags():
        return HttpResponseForbidden("Don't have grades!")

    ags = message_launch.get_ags()
    nrps = message_launch.get_nrps()

    members = nrps.get_members()
    line_items = ags.get_lineitems()
    grades = [ags.get_grades(line_item) for line_item in line_items]
    email = message_launch_data['email']
    try:
        user = BadgeUser.objects.get(email=email, is_teacher=True)
    except BadgeUser.DoesNotExist:
        request.session['lti_context'] = {
            'email': message_launch_data['email'],
            'known_user': False
        }
        return redirect(f"{settings.UI_URL}/lti")

    social_account = user.get_social_account()
    sociallogin = SocialLogin(account=social_account, email_addresses=[email for email in user.email_items])
    sociallogin.user = user
    badgr_app = BadgrApp.objects.filter(pk=user.badgrapp_id).first()
    if not badgr_app:
        badgr_app = BadgrApp.objects.all().first()
    set_session_badgr_app(request, badgr_app)
    ret = perform_login(request, sociallogin.user,
                        email_verification=app_settings.EMAIL_VERIFICATION,
                        redirect_url=sociallogin.get_redirect_url(request),
                        signal_kwargs={"sociallogin": sociallogin})
    return Response({"url": ret.url}, status=status.HTTP_200_OK)

    request.session['lti_context'] = {
        'email': message_launch_data['email'],
        'known_user': True,
        'launch_id': message_launch.get_launch_id(),
        'url':
    }
    return redirect(f"{settings.UI_URL}/lti")


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


def get_lti_context(request):
    return JsonResponse(request.session.get('lti_context'), safe=False)

def render_auth_error(issuer, tool_conf: ToolConfAbstract):
    tool_conf.get_iss_config('issuer')
    extra_context = {}
    institution = Institution.objects.get(identifier=institution_identifier)
    Institution
    if institution and institution.cached_staff():
        cached_staff = institution.cached_staff()
        admins = list(filter(lambda u: u.may_administrate_users, cached_staff))
        if len(admins) > 0:
            extra_context["admin_email"] = admins[0].user.email

    error = 'Sorry, you can not register without an invite.'
    extra_context["code"] = AuthErrorCode.REGISTER_WITHOUT_INVITE
    if request.user.date_joined.today().date() == datetime.datetime.today().date():  # extra protection before deletion
        request.user.delete()
    return render_authentication_error(request, SurfConextProvider.id, error,
                                       extra_context=extra_context)
