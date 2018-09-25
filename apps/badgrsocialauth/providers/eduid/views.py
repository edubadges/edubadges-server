import urllib, requests, json, logging
from base64 import b64encode
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import redirect
from allauth.socialaccount.helpers import render_authentication_error, complete_social_login
from allauth.socialaccount.models import SocialApp
from badgrsocialauth.utils import get_session_auth_token
from .provider import EduIDProvider
logger = logging.getLogger('Badgr.Debug')

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
    # the only thing set in state is the referer (frontend, or staff)
    referer = request.META['HTTP_REFERER'].split('/')[3]
    state = referer
    params = {
    "state": state,
    'redirect_uri': '%s/account/eduid/login/callback/' % settings.HTTP_ORIGIN,
    }
    headers = {
      'Content-Type': "application/json",
      'Cache-Control': "no-cache",
      'Authorization': encode(current_app.client_id, current_app.secret)
    }
    response = requests.post("{}/login".format(settings.EDUID_PROVIDER_URL+'/oidc'), data=json.dumps(params), headers=headers)    
    return redirect(response.text)
    

def callback(request):
    current_app = SocialApp.objects.get_current(provider='edu_id')
    #extract state of redirect
    referer = request.GET.get('state')
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
    response = requests.post("{}/token".format(settings.EDUID_PROVIDER_URL+'/oidc'), data=urllib.parse.urlencode(payload), headers=headers)
    token_json = response.json()
    
    # 2. now with access token we can request userinfo
    headers = {"Authorization": "Bearer " + token_json['access_token'] }
    response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL+'/oidc'), headers=headers)
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    userinfo_json = response.json()
    
    # retrieved data in fields and ensure that email & sub are in extra_data
    if 'email' not in userinfo_json or 'sub' not in userinfo_json:
        error = 'Sorry, your account has no email attached from SurfConext, try another login method.'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error)
    
    # 3. Complete social login 
    provider = EduIDProvider(request)
    login = provider.sociallogin_from_response(request, userinfo_json)
    ret = complete_social_login(request, login)
   
    # 4. Return the user to where she came from (ie the referer: frontend or staff dahsboard)
    if referer == 'staff':
        return HttpResponseRedirect(reverse('admin:index'))
    else:
        return ret

