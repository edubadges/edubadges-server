# encoding: utf-8


from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_302_FOUND, HTTP_204_NO_CONTENT

from backpack.models import BackpackBadgeShare, ImportedAssertion
from backpack.permissions import IsImportedBadgeOwner
from backpack.serializers_v1 import LocalBadgeInstanceUploadSerializerV1, ImportedAssertionSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import BadgeInstance
from issuer.permissions import RecipientIdentifiersMatch, BadgrOAuthTokenHasScope
from mainsite.exceptions import BadgrApiException400
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from public.public_api import ImagePropertyDetailView


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
        fields_whitelist = ('acceptance', 'public', 'include_evidence')
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
            raise BadgrApiException400("Unspecified share provider", 701)
        provider = provider.lower()

        source = request.query_params.get('source', 'unknown')

        badge = self.get_object(request, **kwargs)
        if not badge:
            return Response(status=HTTP_404_NOT_FOUND)

        share = BackpackBadgeShare(provider=provider, badgeinstance=badge, source=source)
        share_url = share.get_share_url(provider)
        if not share_url:
            raise BadgrApiException400("Invalid share provider", 702)

        share.save()

        if redirect:
            headers = {'Location': share_url}
            return Response(status=HTTP_302_FOUND, headers=headers)
        else:
            return Response({'url': share_url})


class ImportedAssertionList(BaseEntityListView):
    model = ImportedAssertion
    serializer_class = ImportedAssertionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ('post', 'get')

    def get_objects(self, request, **kwargs):
        return ImportedAssertion.objects.filter(user=request.user, verified=True)

    def post(self, request, **kwargs):
        """Upload a new Assertion to the backpack"""
        return super(ImportedAssertionList, self).post(request, **kwargs)


class ImportedAssertionDelete(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail, IsImportedBadgeOwner)
    http_method_names = ['delete']
    model = ImportedAssertion


class ImportedAssertionDetail(BaseEntityDetailView):
    model = ImportedAssertion
    serializer_class = ImportedAssertionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ('put')

    def put(self, request, **kwargs):
        """Update verified status if the code is ok"""
        data = request.data
        assertion = ImportedAssertion.objects.filter(user=request.user, code=data['code'],
                                                     entity_id=data['entity_id']).first()
        assertion.verified = True
        assertion.save()
        return Response(data)
