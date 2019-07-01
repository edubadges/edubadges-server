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
from ims.models import LTITenant
from mainsite.models import BadgrApp
from .provider import EduIDProvider
from lti_edu.models import StudentsEnrolled, LtiBadgeUserTennant, UserCurrentContextId
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
        message = {'message':'Found a ":" in username, this is not allowed', 'source': 'eduID login encoding'}
        logger.error(message)
        raise Exception(message)
    username_password = '%s:%s' % (username, password)
    return 'Basic ' + b64encode(username_password.encode()).decode()

def login(request):
    current_app = SocialApp.objects.get_current(provider='edu_id')
    # the only thing set in state is the referer (frontend, or staff) , this is not the referer url.
    referer = json.dumps(urlparse(request.META['HTTP_REFERER']).path.split('/')[1:])
    badgr_app_pk = request.session.get('badgr_app_pk', None)
    try:
        badgr_app_pk = int(badgr_app_pk)
    except:
        badgr_app_pk = settings.BADGR_APP_ID

    lti_data = request.session.get('lti_data', None)
    lti_context_id = ''
    lti_user_id = ''
    lti_roles = ''
    if lti_data is not None:
        lti_context_id= lti_data['lti_context_id']
        lti_user_id = lti_data['lti_user_id']
        lti_roles = lti_data['lti_roles']
    state = json.dumps([referer,badgr_app_pk, lti_context_id,lti_user_id,lti_roles])

    params = {
    "state": state,
    "client_id": current_app.client_id,
    "response_type": "code",
    "scope": "openid",
    'redirect_uri': '%s/account/eduid/login/callback/' % settings.HTTP_ORIGIN,

    }
    return redirect("{}/login?{}".format(settings.EDUID_PROVIDER_URL, urllib.parse.urlencode(params)))


def after_terms_agreement(request, **kwargs):
    '''
    this is the second part of the callback, after consent has been given, or is user already exists
    '''
    badgr_app_pk, login_type, lti_context_id,lti_user_id,lti_roles, referer = json.loads(kwargs['state'])
    lti_data = request.session.get('lti_data', None)

    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)
    set_session_badgr_app(request, badgr_app)

    access_token = kwargs.get('access_token', None)
    if not access_token:
        error = 'Sorry, we could not find your eduID credentials.'
        return render_authentication_error(request, EduIDProvider.id, error)
    
    headers = {"Authorization": "Bearer " + access_token }
    response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL), headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    userinfo_json = response.json()
    
    if 'sub' not in userinfo_json:
        error = 'Sorry, your eduID account has no identifier.'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error)

    social_account = get_social_account(userinfo_json['sub']) 
    if not social_account: # user does not exist
        # ensure that email & names are in extra_data
        if 'email' not in userinfo_json:
            error = 'Sorry, your eduID account does not have your institution mail. Login to eduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
        if 'family_name' not in userinfo_json:
            error = 'Sorry, your eduID account has no family_name attached from SURFconext. Login to eduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
        if 'given_name' not in userinfo_json:
            error = 'Sorry, your eduID account has no first_name attached from SURFconext. Login to eduID and link your institution account, then try again.'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error)
    else: # user already exists
        update_user_params(social_account.user, userinfo_json)
    
    # 3. Complete social login 

    provider = EduIDProvider(request)
    login = provider.sociallogin_from_response(request, userinfo_json)
    ret = complete_social_login(request, login)
    set_session_badgr_app(request, badgr_app)

    #create lti_connection
    if lti_data is not None and 'lti_user_id' in lti_data:
        if not request.user.is_anonymous():
            tenant = LTITenant.objects.get(client_key=lti_data['lti_tenant'])
            badgeuser_tennant, _ = LtiBadgeUserTennant.objects.get_or_create(lti_user_id=lti_data['lti_user_id'],
                                                                             badge_user=request.user,
                                                                             lti_tennant=tenant,
                                                                             staff=False
                                                                            )
            user_current_context_id,_ = UserCurrentContextId.objects.get_or_create(badge_user=request.user)
            user_current_context_id.context_id = lti_data['lti_context_id']
            user_current_context_id.save()
    request.session['lti_user_id'] = lti_user_id
    request.session['lti_roles'] = lti_roles


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
    print(request.__dict__)
    print(request.__dict__['session'].__dict__)
    current_app = SocialApp.objects.get_current(provider='edu_id')
    #extract state of redirect
    state = json.loads(request.GET.get('state'))
    referer, badgr_app_pk, lti_context_id,lti_user_id,lti_roles = state
    lti_data = request.session.get('lti_data', None);

    code = request.GET.get('code', None)  # access codes to access user info endpoint
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
     "client_secret": current_app.secret,
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
                        'state': json.dumps([str(badgr_app_pk), 'edu_id', lti_context_id,lti_user_id,lti_roles]+ [json.loads(referer)]),
                         'after_terms_agreement_url_name': 'eduid_terms_accepted_callback'}

    if not get_social_account(userinfo_json['sub']):
        return HttpResponseRedirect(reverse('accept_terms', kwargs=keyword_arguments))
    
    return after_terms_agreement(request, **keyword_arguments)
