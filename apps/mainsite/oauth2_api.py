# encoding: utf-8


import datetime
import json
import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils import timezone
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.models import get_application_model, get_access_token_model, Application
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views import TokenView as OAuth2ProviderTokenView
from oauth2_provider.views.mixins import OAuthLibMixin
from oauthlib.oauth2.rfc6749.utils import scope_to_list
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_200_OK
from rest_framework.views import APIView

import badgrlog
from badgeuser.authcode import accesstoken_for_authcode
from mainsite.models import ApplicationInfo
from mainsite.oauth_validator import BadgrRequestValidator, BadgrOauthServer
from mainsite.utils import client_ip_from_request

badgrlogger = badgrlog.BadgrLogger()

class AuthorizationSerializer(serializers.Serializer):
    client_id = serializers.CharField(required=True)
    redirect_uri = serializers.URLField(required=True)
    response_type = serializers.CharField(required=False, default=None, allow_null=True)
    state = serializers.CharField(required=False, default=None, allow_null=True)
    scopes = serializers.ListField(child=serializers.CharField())
    allow = serializers.BooleanField(required=True)


class AuthorizationApiView(OAuthLibMixin, APIView):
    permission_classes = []

    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS

    skip_authorization_completely = False

    def get_authorization_redirect_url(self, scopes, credentials, allow=True):
        uri, headers, body, status = self.create_authorization_response(
            request=self.request, scopes=scopes, credentials=credentials, allow=allow)
        return uri

    def post(self, request, *args, **kwargs):
        # Copy/Pasta'd from oauth2_provider.views.BaseAuthorizationView.form_valid
        try:
            serializer = AuthorizationSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            credentials = {
                "client_id": serializer.data.get("client_id"),
                "redirect_uri": serializer.data.get("redirect_uri"),
                "response_type": serializer.data.get("response_type", None),
                "state": serializer.data.get("state", None),
            }

            scopes = ' '.join(serializer.data.get("scopes"))
            allow = serializer.data.get("allow")
            success_url = self.get_authorization_redirect_url(scopes, credentials, allow)
            return Response({ 'success_url': success_url })

        except OAuthToolkitError as error:
            return Response({
                'error': error.oauthlib_error.description
            }, status=HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        # Copy/Pasta'd from oauth2_provider.views.BaseAuthorizationView.get
        try:
            scopes, credentials = self.validate_authorization_request(request)
            # all_scopes = get_scopes_backend().get_all_scopes()
            # kwargs["scopes"] = scopes
            # kwargs["scopes_descriptions"] = [all_scopes[scope] for scope in scopes]
            # at this point we know an Application instance with such client_id exists in the database

            # TODO: Cache this!
            application = get_application_model().objects.get(client_id=credentials["client_id"])

            kwargs["client_id"] = credentials["client_id"]
            kwargs["redirect_uri"] = credentials["redirect_uri"]
            kwargs["response_type"] = credentials["response_type"]
            kwargs["state"] = credentials["state"]
            try:
                kwargs["application"] = {
                    "name": application.applicationinfo.get_visible_name(),
                }
                if application.applicationinfo.icon:
                    kwargs["application"]['image'] = application.applicationinfo.icon.url
                if application.applicationinfo.website_url:
                    kwargs["application"]["url"] = application.applicationinfo.website_url
                app_scopes = [s for s in re.split(r'[\s\n]+', application.applicationinfo.allowed_scopes) if s]
            except ApplicationInfo.DoesNotExist:
                app_scopes = ["r:profile"]
                kwargs["application"] = dict(
                    name=application.name,
                    scopes=app_scopes
                )

            filtered_scopes = set(app_scopes) & set(scopes)
            kwargs['scopes'] = list(filtered_scopes)
            all_scopes = get_scopes_backend().get_all_scopes()
            kwargs['scopes_descriptions'] = {scope: all_scopes[scope] for scope in scopes}

            self.oauth2_data = kwargs

            # Check to see if the user has already granted access and return
            # a successful response depending on "approval_prompt" url parameter
            require_approval = request.GET.get("approval_prompt", oauth2_settings.REQUEST_APPROVAL_PROMPT)

            # If skip_authorization field is True, skip the authorization screen even
            # if this is the first use of the application and there was no previous authorization.
            # This is useful for in-house applications-> assume an in-house applications
            # are already approved.
            if application.skip_authorization:
                success_url = self.get_authorization_redirect_url(" ".join(kwargs['scopes']), credentials)
                return Response({ 'success_url': success_url })

            elif require_approval == "auto" and not request.user.is_anonymous:
                tokens = get_access_token_model().objects.filter(
                    user=request.user,
                    application=application,
                    expires__gt=timezone.now()
                ).all()

                # check past authorizations regarded the same scopes as the current one
                for token in tokens:
                    if token.allow_scopes(scopes):
                        success_url = self.get_authorization_redirect_url(" ".join(kwargs['scopes']), credentials)
                        return Response({ 'success_url': success_url })

            return Response(kwargs)

        except OAuthToolkitError as error:
            return Response({
                'error': error.oauthlib_error.description
            }, status=HTTP_400_BAD_REQUEST)


class TokenView(OAuth2ProviderTokenView):

    server_class = BadgrOauthServer
    validator_class = BadgrRequestValidator

    def post(self, request, *args, **kwargs):

        def _request_identity(request):
            username = request.POST.get('username', None)
            if username:
                return username
            return client_ip_from_request(self.request)

        def _backoff_cache_key(request):
            return "failed_token_backoff_{}".format(_request_identity(request))

        _backoff_period = getattr(settings, 'TOKEN_BACKOFF_PERIOD_SECONDS', 2)

        grant_type = request.POST.get('grant_type', 'password')

        if grant_type == 'password' and _backoff_period is not None:
            # check for existing backoff for password attempts
            backoff = cache.get(_backoff_cache_key(request))
            if backoff is not None:
                backoff_until = backoff.get('until', None)
                backoff_count = backoff.get('count', 1)
                if backoff_until > timezone.now():
                    backoff_count += 1
                    backoff_seconds = min(86400, _backoff_period ** backoff_count)  # maximum backoff is 24 hours
                    backoff_until = timezone.now() + datetime.timedelta(seconds=backoff_seconds)
                    cache.set(_backoff_cache_key(request), dict(until=backoff_until, count=backoff_count), timeout=None)
                    # return the same error as a failed login attempt
                    return HttpResponse(json.dumps({"error_description": "Invalid credentials given.", "error": "invalid_grant"}), status=HTTP_401_UNAUTHORIZED)

        # pre-validate scopes requested
        client_id = request.POST.get('client_id', None)
        requested_scopes = [s for s in scope_to_list(request.POST.get('scope', '')) if s]
        if client_id:
            try:
                oauth_app = Application.objects.get(client_id=client_id)
            except Application.DoesNotExist:
                return HttpResponse(json.dumps({"error": "invalid client_id"}), status=HTTP_400_BAD_REQUEST)

            try:
                allowed_scopes = oauth_app.applicationinfo.scope_list
            except ApplicationInfo.DoesNotExist:
                allowed_scopes = ['r:profile']

            # handle rw:issuer:* scopes
            if 'rw:issuer:*' in allowed_scopes:
                issuer_scopes = [x for x in requested_scopes if x.startswith(r'rw:issuer:')]
                allowed_scopes.extend(issuer_scopes)

            filtered_scopes = set(allowed_scopes) & set(requested_scopes)
            if len(filtered_scopes) < len(requested_scopes):
                return HttpResponse(json.dumps({"error": "invalid scope requested"}), status=HTTP_400_BAD_REQUEST)

        # let parent method do actual authentication
        response = super(TokenView, self).post(request, *args, **kwargs)

        if grant_type == "password" and response.status_code == 401:
            # failed password login attempt
            username = request.POST.get('username', None)
            badgrlogger.event(badgrlog.FailedLoginAttempt(request, username, endpoint='/o/token'))

            if _backoff_period is not None:
                # update backoff for failed logins
                backoff = cache.get(_backoff_cache_key(request))
                if backoff is None:
                    backoff = {'count': 0}
                backoff['count'] += 1
                backoff['until'] = timezone.now() + datetime.timedelta(seconds=_backoff_period ** backoff['count'])
                cache.set(_backoff_cache_key(request), backoff, timeout=None)
        elif response.status_code == 200:
            # successful login
            cache.set(_backoff_cache_key(request), None)  # clear any existing backoff

        return response


class AuthCodeExchange(APIView):
    permission_classes = []

    def post(self, request, **kwargs):
        def _error_response():
            return Response({"error": "Invalid authcode"}, status=HTTP_400_BAD_REQUEST)

        code = request.data.get('code')
        if not code:
            return _error_response()

        accesstoken = accesstoken_for_authcode(code)
        if accesstoken is None:
            return _error_response()

        data = dict(
            access_token=accesstoken.token,
            token_type="Bearer",
            scope=accesstoken.scope
        )

        return Response(data, status=HTTP_200_OK)
