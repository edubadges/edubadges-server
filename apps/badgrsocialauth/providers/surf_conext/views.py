import urllib

import requests
from allauth.socialaccount.helpers import render_authentication_error, complete_social_login
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from badgrsocialauth.utils import set_session_badgr_app, get_session_auth_token, get_verified_user, get_session_badgr_app
from mainsite.models import BadgrApp
from .provider import SurfConextProvider
from institution.models import Institution


def login(request):
    """
    Redirect to login page of SURFconext openID, this is "Where are you from" page

    Note: core differences in OpenID and SurfConext is authentication method and incomplete autodiscovery endpoint.

    :return: HTTP redirect to WAYF
    """

    _current_app = SocialApp.objects.get_current(provider='surf_conext')

    # state contains the data required for the redirect after the login via SurfConext,
    # it contains the user token, type of process and which badge_app
    
    referer = request.META['HTTP_REFERER'].split('/')[3]
    state = '%s-%s-%s-%s' % (request.GET.get('process', 'login'),
                          get_session_auth_token(request),
                          request.session.get('badgr_app_pk', None), 
                          referer)

    data = {'client_id': _current_app.client_id,
            'redirect_uri': '%s/account/openid/login/callback/' % settings.HTTP_ORIGIN,
            'response_type': 'code',

            # SurfConext does not support other scopes, as such the complete OpenID flow is not supported
            'scope': 'openid',
            'state': state
            }
            
    redirect_url = settings.SURFCONEXT_DOMAIN_URL + '/authorize?%s' %  (urllib.urlencode(data))

    print('logging into, redirect', data)
    return HttpResponseRedirect(redirect_url)


@csrf_exempt
def callback(request):
    """
        Callback page, after user returns from "Where are you from" page.
        Due to limited scope support (without tokenized user information) the OpenID workflow is extended.

        Steps:
        1. Exchange callback Token for access token
        2. Retrieve user information with the access token
        3. Complete social login and return to frontend

        Retrieved information:
        - email: Obligated, if not available will fail request
        - sub: optional, string, user code
        - given_name: optional, string
        - family_name: optional, string
        - edu_person_targeted_id: optional
        - schac_home_organization: optional

    :return: Either renders authentication error, or completes the social login
    """
    print('getting callback', request.GET.get('state'))
    # extract the state of the redirect
    process, auth_token, badgr_app_pk, referer = tuple(request.GET.get('state').split('-'))

    # check if code is given
    code = request.GET.get('code', None)
    if code is None:
        error = 'Server error: No userToken found in callback'
        return render_authentication_error(request, SurfConextProvider.id, error=error)

    # 1. Exchange callback Token for access token
    _current_app = SocialApp.objects.get_current(provider='surf_conext')
    data = {'redirect_uri': '%s/account/openid/login/callback/' % settings.HTTP_ORIGIN,
            'client_id': _current_app.client_id,
            'client_secret': _current_app.secret,
            'scope': 'openid',
            'grant_type': 'authorization_code',
            'code': code}

    url =  settings.SURFCONEXT_DOMAIN_URL + '/token?%s' % (urllib.urlencode(data))

    response = requests.post(url)

    if response.status_code != 200:
        error = 'Server error: Token endpoint error (http %s) try alternative login methods' % response.status_code
        return render_authentication_error(request, SurfConextProvider.id, error=error)

    data = response.json()
    access_token = data.get('access_token', None)
    if access_token is None:
        error = 'Server error: No access token, try alternative login methods.'
        return render_authentication_error(request, SurfConextProvider.id, error=error)

    # 2. Retrieve user information with the access token
    headers = {'Authorization': 'bearer %s' % data['access_token']}

    url = settings.SURFCONEXT_DOMAIN_URL + '/userinfo'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        return render_authentication_error(request, SurfConextProvider.id, error=error)

    # retrieved data in fields and ensure that email & sud are in extra_data
    extra_data = response.json()
    print('getting extra data', extra_data)
    if 'email' not in extra_data or 'sub' not in extra_data:
        error = 'Sorry, your account has no email attached from SurfConext, try another login method.'
        return render_authentication_error(request, SurfConextProvider.id, error)
    if "schac_home_organization" not in extra_data:
        error = 'Sorry, your account has no home organization attached from SurfConext, try another login method.'
        return render_authentication_error(request, SurfConextProvider.id, error)

    if 'family_name' in extra_data:
        extra_data['family_name'] = ''
    if 'given_name' in extra_data:
        extra_data['given_name'] = ''
    
    # 3. Complete social login and return to frontend
    provider = SurfConextProvider(request)
    login = provider.sociallogin_from_response(request, extra_data)

    # Reset the badgr app id after login as django overturns it
    set_session_badgr_app(request, BadgrApp.objects.get(pk=badgr_app_pk))

    # connect process in which OpenID connects with, either login or connect, if you connect then login user with token
    login.state = {'process': process}

    # login for connect because socialLogin can only connect to request.user
    if process == 'connect' and request.user.is_anonymous() and auth_token:
        request.user = get_verified_user(auth_token=auth_token)
    
    ret = complete_social_login(request, login)
    institution_name = extra_data['schac_home_organization']
    institution, created = Institution.objects.get_or_create(name=institution_name)
    request.user.institution = institution
    request.user.save()
    # override the response with a redirect to staff dashboard if the login came from there
    if referer == 'staff':
        return HttpResponseRedirect(reverse('admin:index'))
    else:
        return ret
    
