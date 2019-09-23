import urllib, json

import requests
from allauth.socialaccount.helpers import render_authentication_error, complete_social_login
from allauth.socialaccount.models import SocialApp
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse

from badgrsocialauth.utils import set_session_badgr_app, get_session_authcode, get_verified_user, get_session_badgr_app, \
    get_social_account, check_agreed_term_and_conditions
from ims.models import LTITenant
from lti_edu.models import LtiBadgeUserTennant, UserCurrentContextId
from mainsite.models import BadgrApp
from .provider import SurfConextProvider
from institution.models import Institution
from allauth.account.adapter import get_adapter as get_account_adapter

def login(request):
    """
    Redirect to login page of SURFconext openID, this is "Where are you from" page

    Note: core differences in OpenID and SURFconext is authentication method and incomplete autodiscovery endpoint.

    :return: HTTP redirect to WAYF
    """
    lti_data = request.session.get('lti_data', None)
    lti_context_id = ''
    lti_user_id = ''
    lti_roles = ''
    if lti_data is not None:
        lti_context_id = lti_data['lti_context_id']
        lti_user_id = lti_data['lti_user_id']
        lti_roles = lti_data['lti_roles']

    _current_app = SocialApp.objects.get_current(provider='surf_conext')

    # state contains the data required for the redirect after the login via SURFconext,
    # it contains the user token, type of process and which badge_app
    
    referer = request.META['HTTP_REFERER'].split('/')[3]

    badgr_app_pk = request.session.get('badgr_app_pk', None)
    try:
        badgr_app_pk = int(badgr_app_pk)
    except:
        badgr_app_pk = settings.BADGR_APP_ID
    state = json.dumps([request.GET.get('process', 'login'),
                          get_session_authcode(request),
                          badgr_app_pk,
                          lti_context_id,
                          lti_user_id,
                          lti_roles,
                          referer])

    data = {'client_id': _current_app.client_id,
            'redirect_uri': '%s/account/openid/login/callback/' % settings.HTTP_ORIGIN,
            'response_type': 'code',
            # SURFconext does not support other scopes, as such the complete OpenID flow is not supported
            'scope': 'openid',
            'state': state
            }
            
    redirect_url = settings.SURFCONEXT_DOMAIN_URL + '/authorize?%s' %  (urllib.urlencode(data))

    return HttpResponseRedirect(redirect_url)


def after_terms_agreement(request, **kwargs):
    access_token = kwargs.get('access_token', None)
    if not access_token:
        error = 'Sorry, we could not find you SURFconext credentials.'
        return render_authentication_error(request, SurfConextProvider.id, error)
    
    headers = {'Authorization': 'bearer %s' % access_token}
    badgr_app_pk, login_type, process, auth_token, lti_context_id,lti_user_id,lti_roles, referer = json.loads(kwargs['state'])
    try:
        badgr_app_pk = int(badgr_app_pk)
    except:
        badgr_app_pk = settings.BADGR_APP_ID
    set_session_badgr_app(request, BadgrApp.objects.get(pk=badgr_app_pk))

    lti_data = request.session.get('lti_data', None)
    url = settings.SURFCONEXT_DOMAIN_URL + '/userinfo'

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        return render_authentication_error(request, SurfConextProvider.id, error=error)

    # retrieved data in fields and ensure that email & sud are in extra_data
    extra_data = response.json()

    if 'email' not in extra_data or 'sub' not in extra_data:
        error = 'Sorry, your account has no email attached from SURFconext, try another login method.'
        return render_authentication_error(request, SurfConextProvider.id, error)
    if "schac_home_organization" not in extra_data:
        error = 'Sorry, your account has no home organization attached from SURFconext, try another login method.'
        return render_authentication_error(request, SurfConextProvider.id, error)
  
    if 'family_name' in extra_data:
        extra_data['family_name'] = ''
    if 'given_name' in extra_data:
        extra_data['given_name'] = ''
      
    # 3. Complete social login and return to frontend
    provider = SurfConextProvider(request)
    login = provider.sociallogin_from_response(request, extra_data)
  
    # Reset the badgr app id after login as django overturns it

    # connect process in which OpenID connects with, either login or connect, if you connect then login user with token
    login.state = {'process': process}
  
    # login for connect because socialLogin can only connect to request.user
    if process == 'connect' and request.user.is_anonymous() and auth_token:
        request.user = get_verified_user(auth_token=auth_token)
      
    ret = complete_social_login(request, login)
    if not request.user.is_anonymous(): # the social login succeeded
        institution_name = extra_data['schac_home_organization']
        institution, created = Institution.objects.get_or_create(name=institution_name)
        request.user.institution = institution
        request.user.save()
    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)

    resign = True
    check_agreed_term_and_conditions(request.user, badgr_app, resign=resign)

    if lti_data is not None and 'lti_user_id' in lti_data:
        if not request.user.is_anonymous():
            tenant = LTITenant.objects.get(client_key=lti_data['lti_tenant'])
            badgeuser_tennant, _ = LtiBadgeUserTennant.objects.get_or_create(lti_user_id=lti_data['lti_user_id'],
                                                                            badge_user=request.user,
                                                                            lti_tennant=tenant,
                                                                            staff=True)
            user_current_context_id,_ = UserCurrentContextId.objects.get_or_create(badge_user=request.user)
            user_current_context_id.context_id = lti_data['lti_context_id']
            user_current_context_id.save()

    request.session['lti_user_id'] = lti_user_id
    request.session['lti_roles'] = lti_roles
    if not request.user.is_authenticated:
        print(request.__dict__)
        a = 1
    # override the response with a redirect to staff dashboard if the login came from there
    if referer == 'staff':
        return HttpResponseRedirect(reverse('admin:index'))
    else:
        return ret

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
    # extract the state of the redirect
    print(request.__dict__)
    print(request.__dict__['session'].__dict__)

    if request.user.is_authenticated:
        get_account_adapter(request).logout(request)  # logging in while being authenticated breaks the login procedure

    process, auth_token, badgr_app_pk,lti_data,lti_user_id,lti_roles, referer = json.loads(request.GET.get('state'))

    if badgr_app_pk is None:
        print('none here')
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

    keyword_arguments = {'access_token': access_token,
                         'state': json.dumps([badgr_app_pk, 'surf_conext' ,process, auth_token,lti_data, lti_user_id,lti_roles,referer]),
                         'after_terms_agreement_url_name': 'surf_conext_terms_accepted_callback'}
     
    if not get_social_account(extra_data['sub']):
        return HttpResponseRedirect(reverse('accept_terms', kwargs=keyword_arguments))
    social_account = get_social_account(extra_data['sub'])
    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)

    # set_session_badgr_app(request, BadgrApp.objects.get(pk=badgr_app.pk))
    if 'edu_person_affiliations' in extra_data:
        if not ('employee' in extra_data['edu_person_affiliations'] or 'faculty' in extra_data['edu_person_affiliations']):
            error = 'Must be employee or faculty member to login. If You are a student, please login with EduID'
            return render_authentication_error(request, SurfConextProvider.id, error)

    if not check_agreed_term_and_conditions(social_account.user, badgr_app):
        return HttpResponseRedirect(reverse('accept_terms_resign', kwargs=keyword_arguments))

    return after_terms_agreement(request, **keyword_arguments)
