# encoding: utf-8
from __future__ import unicode_literals

from rest_framework import permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST, HTTP_302_FOUND, \
    HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from backpack.models import BackpackCollection, BackpackBadgeShare, BackpackCollectionShare
from backpack.serializers_v1 import CollectionSerializerV1, LocalBadgeInstanceUploadSerializerV1
from backpack.serializers_v2 import BackpackAssertionSerializerV2, BackpackCollectionSerializerV2, \
    BackpackImportSerializerV2
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import BadgeInstance
from issuer.permissions import AuditedModelOwner, VerifiedEmailMatchesRecipientIdentifier
from issuer.public_api import ImagePropertyDetailView
from mainsite.decorators import apispec_list_operation, apispec_post_operation, apispec_get_operation, \
    apispec_delete_operation, apispec_put_operation, apispec_operation
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class BackpackAssertionList(BaseEntityListView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializerV1
    v2_serializer_class = BackpackAssertionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, VerifiedEmailMatchesRecipientIdentifier)
    http_method_names = ('get', 'post')

    def get_objects(self, request, **kwargs):
        return filter(lambda a: (not a.revoked) and a.acceptance != BadgeInstance.ACCEPTANCE_REJECTED,
                      self.request.user.cached_badgeinstances())

    @apispec_list_operation('Assertion',
        summary="Get a list of Assertions in authenticated user's backpack ",
        tags=['Backpack']
    )
    def get(self, request, **kwargs):
        return super(BackpackAssertionList, self).get(request, **kwargs)

    @apispec_post_operation('Assertion', BackpackAssertionSerializerV2,
        summary="Upload a new Assertion to the backpack",
        tags=['Backpack']
    )
    def post(self, request, **kwargs):
        if kwargs.get('version', 'v1') == 'v1':
            return super(BackpackAssertionList, self).post(request, **kwargs)
            
        raise NotImplementedError("use BackpackImportBadge.post instead")

    def get_context_data(self, **kwargs):
        context = super(BackpackAssertionList, self).get_context_data(**kwargs)
        context['format'] = self.request.query_params.get('json_format', 'v1')  # for /v1/earner/badges compat
        return context


class BackpackAssertionDetail(BaseEntityDetailView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializerV1
    v2_serializer_class = BackpackAssertionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, VerifiedEmailMatchesRecipientIdentifier)
    http_method_names = ('get', 'delete', 'put')

    def get_context_data(self, **kwargs):
        context = super(BackpackAssertionDetail, self).get_context_data(**kwargs)
        context['format'] = self.request.query_params.get('json_format', 'v1')  # for /v1/earner/badges compat
        return context

    @apispec_get_operation('Assertion',
        summary="Get detail on an Assertion in the user's Backpack",
        tags=['Backpack']
    )
    def get(self, request, **kwargs):
        return super(BackpackAssertionDetail, self).get(request, **kwargs)

    @apispec_delete_operation('Assertion',
        summary='Remove an assertion from the backpack',
        tags=['Backpack']
    )
    def delete(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        obj.acceptance = BadgeInstance.ACCEPTANCE_REJECTED
        obj.save()
        return Response(status=HTTP_204_NO_CONTENT)

    @apispec_put_operation('Assertion', BackpackAssertionSerializerV2,
        summary="Update acceptance of an Assertion in the user's Backpack",
        tags=['Backpack']
    )
    def put(self, request, **kwargs):
        fields_whitelist = ('acceptance',)
        data = {k: v for k, v in request.data.items() if k in fields_whitelist}
        return super(BackpackAssertionDetail, self).put(request, data=data, **kwargs)


class BackpackAssertionDetailImage(ImagePropertyDetailView):
    model = BadgeInstance
    prop = 'image'


class BackpackCollectionList(BaseEntityListView):
    model = BackpackCollection
    v1_serializer_class = CollectionSerializerV1
    v2_serializer_class = BackpackCollectionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, AuditedModelOwner)

    def get_objects(self, request, **kwargs):
        return self.request.user.cached_backpackcollections()

    @apispec_get_operation('Collection',
        summary='Get a list of Collections',
        tags=['Backpack']
    )
    def get(self, request, **kwargs):
        return super(BackpackCollectionList, self).get(request, **kwargs)

    @apispec_post_operation('Collection', BackpackCollectionSerializerV2,
        summary='Create a new Collection',
        tags=['Backpack']
    )
    def post(self, request, **kwargs):
        return super(BackpackCollectionList, self).post(request, **kwargs)


class BackpackCollectionDetail(BaseEntityDetailView):
    model = BackpackCollection
    v1_serializer_class = CollectionSerializerV1
    v2_serializer_class = BackpackCollectionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, AuditedModelOwner)

    @apispec_get_operation('Collection',
        summary='Get a single Collection',
        tags=['Backpack']
    )
    def get(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).get(request, **kwargs)

    @apispec_put_operation('Collection', BackpackCollectionSerializerV2,
        summary='Update a Collection',
        tags=['Backpack']
    )
    def put(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).put(request, **kwargs)

    @apispec_delete_operation('Collection',
        summary='Delete a collection',
        tags=['Backpack']
    )
    def delete(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).delete(request, **kwargs)


class BackpackImportBadge(BaseEntityListView):
    v2_serializer_class = BackpackImportSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ('post',)

    @apispec_operation(
        summary="Import a new Assertion to the backpack",
        tags=['Backpack'],
        parameters=[
            {
                "in": "body",
                "name": "body",
                "required": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "format": "url",
                            "description": "URL to an OpenBadge compliant badge",
                            'required': False
                        },
                        "image": {
                            'type': "string",
                            'format': "data:image/png;base64",
                            'description': "base64 encoded Baked OpenBadge image",
                            'required': False
                        },
                        "assertion": {
                            'type': "json",
                            'description': "OpenBadge compliant json",
                            'required': False
                        },
                    }
                },
            }
        ]
    )
    def post(self, request, **kwargs):
        return super(BackpackImportBadge, self).post(request, **kwargs)


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
        provider = request.query_params.get('provider')

        badge = self.get_object(request, **kwargs)
        if not badge:
            return Response(status=HTTP_404_NOT_FOUND)

        share = BackpackBadgeShare(provider=provider, badgeinstance=badge)
        share_url = share.get_share_url(provider)
        if not share_url:
            return Response({'error': "invalid share provider"}, status=HTTP_400_BAD_REQUEST)

        share.save()
        headers = {'Location': share_url}
        return Response(status=HTTP_302_FOUND, headers=headers)


class ShareBackpackCollection(BaseEntityDetailView):
    model = BackpackCollection
    permission_classes = (permissions.AllowAny,)  # this is AllowAny to support tracking sharing links in emails
    http_method_names = ('get',)

    def get(self, request, **kwargs):
        """
        Share a collection to a supported share provider
        ---
        parameters:
            - name: provider
              description: The identifier of the provider to use. Supports 'facebook', 'linkedin'
              required: true
              type: string
              paramType: query
        """
        provider = request.query_params.get('provider')

        collection = self.get_object(request, **kwargs)
        if not collection:
            return Response(status=HTTP_404_NOT_FOUND)

        share = BackpackCollectionShare(provider=provider, collection=collection)
        share_url = share.get_share_url(provider, title=collection.name, summary=collection.description)
        if not share_url:
            return Response({'error': "invalid share provider"}, status=HTTP_400_BAD_REQUEST)

        share.save()
        headers = {'Location': share_url}
        return Response(status=HTTP_302_FOUND, headers=headers)
