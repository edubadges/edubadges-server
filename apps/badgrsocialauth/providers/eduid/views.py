import urllib, requests, json, logging, os
from urlparse import urlparse, urlsplit
from base64 import b64encode
from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from allauth.socialaccount.helpers import render_authentication_error, complete_social_login
from allauth.socialaccount.models import SocialApp
from badgrsocialauth.utils import set_session_badgr_app, get_social_account, update_user_params
from mainsite.models import BadgrApp
from .provider import EduIDProvider
from lti_edu.models import StudentsEnrolled
from issuer.models import BadgeClass
logger = logging.getLogger('Badgr.Debug')

def enroll_student(user, edu_id, badgeclass_slug):
    badge_class = get_object_or_404(BadgeClass, entity_id=badgeclass_slug)
    # consent given wehen enrolling
    defaults = {'date_consent_given': timezone.now(),
                'first_name': user.first_name, 
                'last_name': user.last_name}
    if user.may_enroll(badge_class):
        StudentsEnrolled.objects.create(badge_class=badge_class, 
                                        email=user.email, 
                                        edu_id=edu_id, 
                                        **defaults)
    return 'enrolled'
    

def encode(username, password): #client_id, secret
    """Returns an HTTP basic authentication encrypted string given a valid
    username and password.
    """
    if ':' in username:
        message = {'message':'Found a ":" in username, this is not allowed', 'source': 'EduID login encoding'}
        logger.error(message)
        raise Exception(message)
    username_password = '%s:%s' % (username, password)
    return 'Basic ' + b64encode(username_password.encode()).decode()

def login(request):
    current_app = SocialApp.objects.get_current(provider='edu_id')
    # the only thing set in state is the referer (frontend, or staff) , this is not the referer url.
    referer = json.dumps(urlparse(request.META['HTTP_REFERER']).path.split('/')[1:])
    badgr_app_pk = request.session.get('badgr_app_pk', None)
    state = json.dumps([referer,badgr_app_pk])
    try:
        referrer_url = request.META['HTTP_REFERER']
        referer_parsed = urlsplit(referrer_url)
        port = request.META['SERVER_PORT']
        referer_domain = referer_parsed.hostname
        redirect_domain = Site.objects.get(domain=referer_domain).domain # check if it's a registered site (if not it will raise an exception)
        scheme = request.is_secure() and "https" or "http" # get the right scheme
        redirect_domain = '{}://{}'.format(scheme,redirect_domain)

        if port != 80:
            redirect_domain = "{}:{}".format(redirect_domain, port) # if port is not 8- add port to redirect url

    except Exception as e:
        redirect_domain = settings.HTTP_ORIGIN
    params = {
    "state": state,
    "client_id": current_app.client_id,
    "response_type": "code",
    "scope": "openid",
    'redirect_uri': '%s/account/eduid/login/callback/'  % settings.HTTP_ORIGIN,
# this part needs fixing        
#    'redirect_uri': '%s/account/eduid/login/callback/'     % redirect_domain,
    }
    return redirect("{}/login?{}".format(settings.EDUID_PROVIDER_URL, urllib.parse.urlencode(params)))

def after_terms_agreement(request, **kwargs):
    '''
    this is the second part of the callback, after consent has been given, or is user already exists
    '''
    badgr_app_pk, login_type, referer = json.loads(kwargs['state'])
    access_token = kwargs.get('access_token', None)
    if not access_token:
        error = 'Sorry, we could not find your EduID credentials.'
        return render_authentication_error(request, EduIDProvider.id, error)
    
    headers = {"Authorization": "Bearer " + access_token }
    response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL), headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    userinfo_json = response.json()
    
    if 'sub' not in userinfo_json:
        error = 'Sorry, your EduID account has no identifier.'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error)

    social_account = get_social_account(userinfo_json['sub']) 
    if not social_account: # user does not exist
        # ensure that email & names are in extra_data
        if 'email' not in userinfo_json:
            error = 'Sorry, your EduID account does not have your institution mail. Login to EduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
        if 'family_name' not in userinfo_json:
            error = 'Sorry, your EduID account has no family_name attached from SurfConext. Login to EduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
        if 'given_name' not in userinfo_json:
            error = 'Sorry, your EduID account has no first_name attached from SurfConext. Login to EduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
    else: # user already exists
        update_user_params(social_account.user, userinfo_json)
    
    # 3. Complete social login 
    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)
    set_session_badgr_app(request, badgr_app)
    provider = EduIDProvider(request)
    login = provider.sociallogin_from_response(request, userinfo_json)
    ret = complete_social_login(request, login)
    
    # 4. Return the user to where she came from (ie the referer: public enrollment or main page)
    if 'public' in referer:
        if 'badges' in referer:
            badgeclass_slug = referer[-1]
            if badgeclass_slug:
                edu_id = userinfo_json['sub']
                enrolled = enroll_student(request.user, edu_id, badgeclass_slug)
        url = ret.url+'&public=true'+'&badgeclassSlug='+badgeclass_slug+'&enrollmentStatus='+enrolled
        return HttpResponseRedirect(url)
    else:
        return ret

def callback(request):
    current_app = SocialApp.objects.get_current(provider='edu_id')
    #extract state of redirect
    state = json.loads(request.GET.get('state'))
    referer, badgr_app_pk = state
    code = request.GET.get('code', None) # access codes to access user info endpoint
    if code is None: #check if code is given
        error = 'Server error: No userToken found in callback'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    
    # 1. Exchange callback Token for access token
    payload = {
     "grant_type": "authorization_code",
    "redirect_uri": '%s/account/eduid/login/callback/' % settings.HTTP_ORIGIN,
     "code": code,
     "client_id": current_app.client_id,
     "client_secret": current_app.secret
    }
    headers = {'Content-Type': "application/x-www-form-urlencoded",
               'Cache-Control': "no-cache"
    }
    response = requests.post("{}/token".format(settings.EDUID_PROVIDER_URL), data=urllib.parse.urlencode(payload), headers=headers)
    token_json = response.json()
    
    # 2. now with access token we can request userinfo
    headers = {"Authorization": "Bearer " + token_json['access_token'] }
    response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL), headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    userinfo_json = response.json()
    
    keyword_arguments = {'access_token':token_json['access_token'], 
                        'state': json.dumps([str(badgr_app_pk), 'edu_id']+ [json.loads(referer)]),
                         'after_terms_agreement_url_name': 'eduid_terms_accepted_callback'}
    if not get_social_account(userinfo_json['sub']):
        return HttpResponseRedirect(reverse('accept_terms', kwargs=keyword_arguments))
    
    return after_terms_agreement(request, **keyword_arguments)
