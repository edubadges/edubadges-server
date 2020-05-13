# encoding: utf-8


from backpack.models import BackpackBadgeShare
from backpack.serializers_v1 import LocalBadgeInstanceUploadSerializerV1
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import BadgeInstance
from issuer.permissions import RecipientIdentifiersMatch, BadgrOAuthTokenHasScope
from issuer.public_api import ImagePropertyDetailView
from mainsite.exceptions import BadgrApiException400
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_302_FOUND, HTTP_204_NO_CONTENT


class BackpackAssertionList(BaseEntityListView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, RecipientIdentifiersMatch)
    http_method_names = ('post',)

    def post(self, request, **kwargs):
        """Upload a new Assertion to the backpack"""
        return super(BackpackAssertionList, self).post(request, **kwargs)


class BackpackAssertionDetail(BaseEntityDetailView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, RecipientIdentifiersMatch)
    http_method_names = ('delete', 'put')

    def delete(self, request, **kwargs):
        """Remove an assertion from the backpack"""
        obj = self.get_object(request, **kwargs)
        obj.acceptance = BadgeInstance.ACCEPTANCE_REJECTED
        obj.public = False
        obj.save()
        return Response(status=HTTP_204_NO_CONTENT)

    def put(self, request, **kwargs):
        """Update acceptance of an Assertion in the user's Backpack and make public / private """
        fields_whitelist = ('acceptance', 'public')
        data = {k: v for k, v in list(request.data.items()) if k in fields_whitelist}
        return super(BackpackAssertionDetail, self).put(request, data=data, **kwargs)


class BackpackAssertionDetailImage(ImagePropertyDetailView, BadgrOAuthTokenHasScope):
    model = BadgeInstance
    prop = 'image'
    valid_scopes = ['r:backpack', 'rw:backpack']


class ShareBackpackAssertion(BaseEntityDetailView):
    model = BadgeInstance
    permission_classes = (permissions.AllowAny,)  # this is AllowAny to support tracking sharing links in emails
    http_method_names = ('get',)

    def get(self, request, **kwargs):
        """
        Share a single badge to a support share provider
        ---
        parameters:
            - name: provider
              description: The identifier of the provider to use. Supports 'facebook', 'linkedin'
              required: true
              type: string
              paramType: query
        """
        # from recipient.api import _scrub_boolean
        redirect = request.query_params.get('redirect', "1")

        provider = request.query_params.get('provider')
        if not provider:
            fields = {'error_message': "Unspecified share provider", 'error_code': 701}
            raise BadgrApiException400(fields)
        provider = provider.lower()

        source = request.query_params.get('source', 'unknown')

        badge = self.get_object(request, **kwargs)
        if not badge:
            return Response(status=HTTP_404_NOT_FOUND)

        share = BackpackBadgeShare(provider=provider, badgeinstance=badge, source=source)
        share_url = share.get_share_url(provider)
        if not share_url:
            fields = {'error_message': "Invalid share provider", 'error_code': 702}
            raise BadgrApiException400(fields)

        share.save()

        if redirect:
            headers = {'Location': share_url}
            return Response(status=HTTP_302_FOUND, headers=headers)
        else:
            return Response({'url': share_url})
