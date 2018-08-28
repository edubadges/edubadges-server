import os, urllib, requests, json
from uuid import uuid4
from base64 import b64encode
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from allauth.socialaccount.models import SocialApp
# from .provider import EduIDProvider

def register():
    '''
    register relying party (this application)
    save your CLIENT_ID and CLIENT_SECRET, these are temporary (must be reset whenever eduID reboots/crashes)
    whenever a call to eduID fails, re-register Badgr, try again
    '''
    current_app = SocialApp.objects.get_current(provider='surf_conext')
    payload = {
    'client_name': settings.EDUID_RELYING_PARTY_NAME,
    'client_uri': settings.EDUID_RELYING_PARTY_HOST,
    'grant_types': [ "authorization_code" ],
    'response_types': ["code"],
    'redirect_uris': [ settings.EDUID_REDIRECT_URL ],
    'scope': "openid",
    'token_endpoint_auth_method': "client_secret_basic"
    }
    headers = {
    'Content-Type': "application/json",
    'Cache-Control': "no-cache"
    }
    response = requests.post("{}/registration".format(settings.EDUID_PROVIDER_URL), json=payload, headers=headers)
    my_registration = response.json()
#     os.environ['EDUID_CLIENT_ID'] = my_registration['client_id']
#     os.environ['EDUID_CLIENT_SECRET'] = my_registration['client_secret']
    current_app.client_id = my_registration['client_id']
    current_app.client_secret = my_registration['client_secret']
 

def encode(username, password): #client_id, secret
    """Returns an HTTP basic authentication encrypted string given a valid
    username and password.
    """
    if ':' in username:
#         raise EncodeError
        raise Exception
    username_password = '%s:%s' % (username, password)
    return 'Basic ' + b64encode(username_password.encode()).decode()

def login(request):
    current_app = SocialApp.objects.get_current(provider='surf_conext')
    register()
    state = str(uuid4()) # not used now, is to check to see if the callback matches the login and is not from another one
    params = {
        "provider": settings.EDUID_PROVIDER_URL + '/oidc',
        #       "client_id": os.environ.get('EDUID_CLIENT_ID', ''),
        "client_id": current_app.client_id,
        "response_type": "code",
        "state": state,
        "redirect_uri": settings.EDUID_REDIRECT_URL,
        "duration": "temporary",
        "scope": "openid"
    }
    url = settings.EDUID_PROVIDER_URL +"/login?" + str(urllib.parse.urlencode(params))
    response = redirect(url)
    response['Authorization'] = encode(os.environ.get('EDUID_CLIENT_ID',''), os.environ.get('EDUID_CLIENT_SECRET',''))
    return response    

def callback(request, error = None):
    try:
        credentials = request.args.get('code') # access codes to acces user infor endpoint
        headers = {"Authorization": "bearer " + credentials}
        response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL+'/oidc'), headers=headers)
        me_json = response.json()
        return HttpResponse(me_json, 200)
    except Exception as e:
        return HttpResponse(json.dumps({'request': request.path, 'args': request.args, 'headers': request.headers.to_list(), 'exception': str(e) }), 200)

# def callback(request, error = None):
#     authentication_response = response.json()
#     os.environ['EDUID_CODE'] = authentication_response['code'] # access codes to acces user infor endpoint
#     headers = {"Authorization": "bearer " + os.environ.get('EDUID_CODE', '')}    
#     response = requests.get("{}/userinfo".format(settings.EDUID_PROVIDER_URL+'/oidc'), headers=headers)
#     
#     me_json = response.json()
# #     return make_response(me_json, 200)
#     return HttpResponse(me_json, 200)

