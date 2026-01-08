import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from base64 import b64encode
from urllib.parse import urlparse

import requests
from allauth.account.adapter import get_adapter as get_account_adapter
from allauth.socialaccount.helpers import (
    render_authentication_error,
    complete_social_login,
)
from django.conf import settings
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from jose import jwt

from badgeuser.models import BadgeUser
from badgrsocialauth.providers.eduid.signals import val_name_audit_trail_signal
from badgrsocialauth.utils import (
    set_session_badgr_app,
    get_social_account,
    update_user_params,
)
from issuer.models import BadgeClass, BadgeInstance
from mainsite.models import BadgrApp
from .provider import EduIDProvider

logger = logging.getLogger('Badgr.Debug')


def encode(username, password):  # client_id, secret
    """Returns an HTTP basic authentication encrypted string given a valid
    username and password.
    """
    if ':' in username:
        message = {
            'message': 'Found a ":" in username, this is not allowed',
            'source': 'eduID login encoding',
        }
        logger.error(message)
        raise Exception(message)
    username_password = '%s:%s' % (username, password)
    return 'Basic ' + b64encode(username_password.encode()).decode()


def login(request):
    badgr_app_pk = request.session.get('badgr_app_pk', None)
    try:
        badgr_app_pk = int(badgr_app_pk)
    except:
        badgr_app_pk = settings.BADGR_APP_ID

    state = json.dumps([badgr_app_pk])

    params = {
        'state': state,
        'client_id': settings.EDU_ID_CLIENT,
        'response_type': 'code',
        'scope': 'openid eduid.nl/links',
        'redirect_uri': f'{settings.HTTP_ORIGIN}/account/eduid/login/callback/',
        'claims': '{"id_token":{"preferred_username":null,"given_name":null,"family_name":null,"email":null,'
        '"eduid":null, "eduperson_scoped_affiliation":null, "preferred_username":null, "uids":null}}',
    }
    validate_name = request.GET.get('validateName')
    if validate_name and validate_name.lower() == 'true':
        params['acr_values'] = 'https://eduid.nl/trust/validate-names'
    if request.GET.get('force_login') == 'True':
        params['prompt'] = 'login'
    args = urllib.parse.urlencode(params)
    # Redirect to eduID and enforce a linked SURFconext user with validated names
    login_url = f'{settings.EDUID_PROVIDER_URL}/authorize?{args}'
    return redirect(login_url)


def callback(request):
    if request.user.is_authenticated:
        get_account_adapter(request).logout(request)  # logging in while being authenticated breaks the login procedure

    # extract state of redirect
    state_param = request.GET.get('state')
    if not state_param:
        error = request.GET.get('error_description', 'Server error: eduID login failed')
        return render_authentication_error(request, EduIDProvider.id, error=error)
    state = json.loads(state_param)
    badgr_app_pk = state[0]
    code = request.GET.get('code', None)  # access codes to access user info endpoint
    if code is None:  # check if code is given
        error = 'Server error: No userToken found in callback'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    # 1. Exchange callback Token for access token
    payload = {
        'grant_type': 'authorization_code',
        'redirect_uri': '%s/account/eduid/login/callback/' % settings.HTTP_ORIGIN,
        'code': code,
        'client_id': settings.EDU_ID_CLIENT,
        'client_secret': settings.EDU_ID_SECRET,
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache',
    }
    token_url = f'{settings.EDUID_PROVIDER_URL}/token'
    response = requests.post(
        token_url,
        data=urllib.parse.urlencode(payload),
        headers=headers,
        timeout=60,
    )
    if response.status_code != 200:
        error = 'Server error: User info endpoint error (http %s). Try alternative login methods' % response.status_code
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)

    token_json = response.json()
    id_token = token_json['id_token']
    access_token = token_json['access_token']
    payload = jwt.get_unverified_claims(id_token)

    social_account = get_social_account(payload[settings.EDUID_IDENTIFIER])

    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)

    keyword_arguments = {
        'id_token': id_token,
        'access_token': access_token,
        'provider': 'eduid',
        'eduperson_scoped_affiliation': payload.get('eduperson_scoped_affiliation', []),
        'state': json.dumps([str(badgr_app_pk), 'edu_id']),
        'role': 'student',
    }

    if not social_account or not social_account.user.general_terms_accepted():
        # Here we redirect to client, but we need to check if there is a validated account
        headers = {
            'Accept': 'application/json, application/json;charset=UTF-8',
            'Authorization': f'Bearer {access_token}',
        }
        eduid_url = f'{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links'
        response = requests.get(eduid_url, headers=headers, timeout=60)
        if response.status_code != 200:
            error = f'Server error: eduID eppn endpoint error ({response.status_code})'
            logger.debug(error)
            return render_authentication_error(request, EduIDProvider.id, error=error)
        eppn_json = response.json()
        validated_name = bool([info['validated_name'] for info in eppn_json if 'validated_name' in info])
        signup_redirect = badgr_app.signup_redirect
        args = urllib.parse.urlencode(keyword_arguments)
        if not validated_name:
            validate_redirect = signup_redirect.replace('signup', 'validate')
            return HttpResponseRedirect(f'{validate_redirect}?{args}')

        keyword_arguments['re_sign'] = False if not social_account else True
        return HttpResponseRedirect(f'{signup_redirect}?{args}')

    return after_terms_agreement(request, **keyword_arguments)


def after_terms_agreement(request, **kwargs):
    """
    this is the second part of the callback, after consent has been given, or is user already exists
    """
    badgr_app_pk, _login_type = json.loads(kwargs['state'])
    try:
        badgr_app_pk = int(badgr_app_pk)
    except:
        badgr_app_pk = settings.BADGR_APP_ID

    badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)
    set_session_badgr_app(request, badgr_app)

    id_token = kwargs.get('id_token', None)
    if not id_token:
        error = 'Sorry, we could not find your eduID credentials.'
        return render_authentication_error(request, EduIDProvider.id, error)
    payload = jwt.get_unverified_claims(id_token)

    logger.info(f'Using payload attribute {settings.EDUID_IDENTIFIER} for unique identifier')

    social_account = get_social_account(payload[settings.EDUID_IDENTIFIER])
    if not social_account:  # user does not exist
        # Fail fast if not all required attribbutes are there
        for attr in [settings.EDUID_IDENTIFIER, 'email', 'family_name', 'given_name']:
            if attr not in payload:
                error = f'Sorry, your eduID account does not have a {attr} attribute. Login to eduID and then try again'
                logger.error(error)
                return render_authentication_error(request, EduIDProvider.id, error)
    else:  # user already exists
        update_user_params(social_account.user, payload)

    # 3. Complete social login
    payload['email'] = payload['email'].lower()
    provider = EduIDProvider(request)
    login = provider.sociallogin_from_response(request, payload)

    ret = complete_social_login(request, login)
    new_url = ret.url + '&role=student'
    ret = HttpResponseRedirect(new_url)

    set_session_badgr_app(request, badgr_app)

    request.user.accept_general_terms()

    logger.info(f'payload from surfconext {json.dumps(payload)}')

    if 'acr' in payload and payload['acr'] == 'https://eduid.nl/trust/validate-names':
        request.user.validated_name = f'{payload["given_name"]} {payload["family_name"]}'
        logger.info(f'Stored validated name {payload["given_name"]} {payload["family_name"]}')

    access_token = kwargs.get('access_token', None)
    headers = {
        'Accept': 'application/json, application/json;charset=UTF-8',
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(f'{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links', headers=headers, timeout=60)
    if response.status_code != 200:
        error = f'Server error: eduID eppn endpoint error ({response.status_code})'
        logger.debug(error)
        return render_authentication_error(request, EduIDProvider.id, error=error)
    eppn_json = response.json()
    request.user.clear_affiliations()
    for info in eppn_json:
        if 'eppn' in info and 'schac_home_organization' in info:
            request.user.add_affiliations(
                [
                    {
                        'eppn': info['eppn'].lower(),
                        'schac_home': info['schac_home_organization'],
                    }
                ]
            )
            logger.info(f'Stored affiliations {info["eppn"]} {info["schac_home_organization"]}')
    validated_names = [info['validated_name'] for info in eppn_json if 'validated_name' in info]
    if request.user.validated_name and len(validated_names) == 0:
        ret = HttpResponseRedirect(ret.url + '&revalidate-name=true')
    if len(validated_names) > 0:
        # Use the preferred linked account for the validated_name.
        preferred_validated_name = [info['validated_name'] for info in eppn_json if info['preferred']]
        if not preferred_validated_name:
            # This should never happen as it would be a bug in eduID, but let's be defensive
            preferred_validated_name = [validated_names[0]]
        val_name_audit_trail_signal.send(
            sender=request.user.__class__,
            user=request.user,
            old_validated_name=request.user.validated_name,
            new_validated_name=preferred_validated_name[0],
        )
        request.user.validated_name = preferred_validated_name[0]
    else:
        val_name_audit_trail_signal.send(
            sender=request.user.__class__,
            user=request.user,
            old_validated_name=request.user.validated_name,
            new_validated_name=None,
        )
        request.user.validated_name = None
    request.user.save()

    if not social_account:
        # This fails if there is already a User account with that email, so we need to delete the old one
        try:
            user = BadgeUser.objects.filter(is_teacher=False, email=payload['email']).exclude(id=login.user.id).first()
            if user:
                user.delete()
        except BadgeUser.DoesNotExist:
            pass

        # We don't create welcome badges anymore

    return ret


def create_edu_id_badge_instance(social_login):
    user = social_login.user
    super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
    badge_class = BadgeClass.objects.get(name=settings.EDUID_BADGE_CLASS_NAME)

    # Issue first badge for user
    badge_class.issue(
        recipient=user,
        created_by=super_user,
        allow_uppercase=True,
        enforce_validated_name=False,
        recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
        expires_at=None,
        extensions=None,
    )
    logger.info(f'Assertion created for {user.email} based on {badge_class.name}')


from django.contrib.auth.signals import user_logged_out, user_logged_in


def print_logout_message(sender, user, request, **kwargs):
    print('user logged out')


def print_login_message(sender, user, request, **kwargs):
    print('user logged in')

if not getattr(settings, 'DISABLE_AUTH_SIGNALS', False):
    user_logged_out.connect(print_logout_message)
    user_logged_in.connect(print_login_message)
