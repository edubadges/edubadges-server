# encoding: utf-8
from __future__ import unicode_literals

from django.utils import timezone
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.http import HttpResponseUriRedirect
from oauth2_provider.models import get_application_model, get_access_token_model
from oauth2_provider.scopes import get_scopes_backend
from oauth2_provider.settings import oauth2_settings
from oauth2_provider.views.mixins import OAuthLibMixin
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView

from mainsite.models import ApplicationInfo


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
                kwargs["scopes"] = scopes = application.applicationinfo.allowed_scopes.split(" ")
            except ApplicationInfo.DoesNotExist:
                kwargs["application"] = dict(
                    name=application.name,
                    scopes=["r:profile"]
                )

            self.oauth2_data = kwargs

            # Check to see if the user has already granted access and return
            # a successful response depending on "approval_prompt" url parameter
            require_approval = request.GET.get("approval_prompt", oauth2_settings.REQUEST_APPROVAL_PROMPT)

            # If skip_authorization field is True, skip the authorization screen even
            # if this is the first use of the application and there was no previous authorization.
            # This is useful for in-house applications-> assume an in-house applications
            # are already approved.
            if application.skip_authorization:
                success_url = self.get_authorization_redirect_url(" ".join(scopes), credentials)
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
                        success_url = self.get_authorization_redirect_url(" ".join(scopes), credentials)
                        return Response({ 'success_url': success_url })

            return Response(kwargs)

        except OAuthToolkitError as error:
            return Response({
                'error': error.oauthlib_error.description
            }, status=HTTP_400_BAD_REQUEST)
