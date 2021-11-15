import os
import urllib.parse
from urllib.parse import parse_qs
from urllib.parse import urlparse

from allauth.account.utils import perform_login
from allauth.socialaccount import app_settings
from allauth.socialaccount.models import SocialLogin
from django.conf import settings
from django.core.cache import caches  # type: ignore
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from pylti1p3.contrib.django import DjangoOIDCLogin, DjangoMessageLaunch
from pylti1p3.launch_data_storage.cache import CacheDataStorage
from pylti1p3.tool_config import ToolConfJsonFile

from badgeuser.models import BadgeUser
from badgrsocialauth.utils import set_session_badgr_app
from institution.models import Institution
from lti13.config import DjangoDbToolConf
from mainsite import TOP_DIR
from mainsite.models import BadgrApp


class DjangoNoSessionCacheDataStorage(CacheDataStorage):
    _cache = None

    def __init__(self, cache_name='default', **kwargs):
        self._cache = caches[cache_name]
        super(DjangoNoSessionCacheDataStorage, self).__init__(cache_name, **kwargs)

    def get_session_cookie_name(self):
        # We are stateless as the client and server do not share the domain
        return None


def get_tool_conf():
    return DjangoDbToolConf()
    # lti_config_path = os.path.join(TOP_DIR, 'apps', 'lti13', 'config', 'lms.json')
    # tool_conf = ToolConfJsonFile(lti_config_path)
    # return tool_conf


def get_launch_data_storage():
    return DjangoNoSessionCacheDataStorage()


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
    message_launch = DjangoMessageLaunch(request, tool_conf, launch_data_storage=launch_data_storage,
                                         deployment_validation=False)
    message_launch_data = message_launch.get_launch_data()
    # Get the mandatory data from the launch data
    email = message_launch_data['email']
    issuer = message_launch_data['iss']
    client_id = message_launch_data['aud']
    # This can not fail as the launch would have been aborted
    registration = tool_conf.find_registration_by_params(issuer, client_id)
    institution = Institution.objects.get(identifier=registration.get_institution_identifier())
    launch_id = message_launch.get_launch_id()
    if not institution:
        return redirect(f"{settings.UI_URL}/lti?status=invalid_institution")

    try:
        user = BadgeUser.objects.get(email=email, is_teacher=True, institution=institution)
    except BadgeUser.DoesNotExist:
        args = {"status": "failure"}
        if institution.cached_staff():
            cached_staff = institution.cached_staff()
            admins = list(filter(lambda u: u.may_administrate_users, cached_staff))
            if len(admins) > 0:
                args["admin_email"] = admins[0].user.email
        return redirect(f"{settings.UI_URL}/lti?{urllib.parse.urlencode(args)}")

    social_account = user.get_social_account()
    social_login = SocialLogin(account=social_account, email_addresses=[email for email in user.email_items])
    social_login.user = user
    badgr_app = BadgrApp.objects.all().first()
    set_session_badgr_app(request, badgr_app)
    ret = perform_login(request, social_login.user,
                        email_verification=app_settings.EMAIL_VERIFICATION,
                        redirect_url=social_login.get_redirect_url(request),
                        signal_kwargs={"sociallogin": social_login})
    auth_token = parse_qs(urlparse(ret.url).query)['authToken'][0]
    args = {"status": "success", "launch_id": launch_id, "auth_token": auth_token}
    return redirect(f"{settings.UI_URL}/lti?{urllib.parse.urlencode(args)}")


def get_jwks(request):
    tool_conf = get_tool_conf()
    return JsonResponse(tool_conf.get_jwks(), safe=False)


def get_lti_context(request, launch_id):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    message_launch = DjangoMessageLaunch.from_cache(launch_id, request, tool_conf,
                                                    launch_data_storage=launch_data_storage)
    launch_data = message_launch.get_launch_data()
    return JsonResponse(launch_data, safe=False)


def get_grades(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    lti_context = request.session.get('lti_context')
    message_launch = DjangoMessageLaunch.from_cache(lti_context.get('launch_id'), request, tool_conf,
                                                    launch_data_storage=launch_data_storage)
    ags = message_launch.get_ags()
    line_items = ags.get_lineitems()
    grades = [ags.get_grades(line_item) for line_item in line_items]
    return JsonResponse(grades, safe=False)


def get_members(request):
    tool_conf = get_tool_conf()
    launch_data_storage = get_launch_data_storage()
    lti_context = request.session.get('lti_context')
    message_launch = DjangoMessageLaunch.from_cache(lti_context.get('launch_id'), request, tool_conf,
                                                    launch_data_storage=launch_data_storage)
    nrps = message_launch.get_nrps()
    members = nrps.get_members()
    return JsonResponse(members, safe=False)
