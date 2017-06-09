# encoding: utf-8
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from backpack.models import BackpackCollection
from backpack.serializers_v2 import BackpackAssertionSerializerV2, BackpackCollectionSerializerV2, \
    BackpackImportSerializerV2
from composition.serializers import LocalBadgeInstanceUploadSerializer, CollectionSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView, BaseEntityView
from issuer.models import BadgeInstance
from issuer.permissions import AuditedModelOwner, VerifiedEmailMatchesRecipientIdentifier
from issuer.public_api import ImagePropertyDetailView
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class BackpackAssertionList(BaseEntityListView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializer
    v2_serializer_class = BackpackAssertionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, VerifiedEmailMatchesRecipientIdentifier)
    http_method_names = ('get',)

    def get_objects(self, request, **kwargs):
        return filter(lambda a: a.acceptance != BadgeInstance.ACCEPTANCE_REJECTED,
                      self.request.user.cached_badgeinstances())

    def get(self, request, **kwargs):
        return super(BackpackAssertionList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        raise NotImplementedError("use BackpackImportBadge.post instead")


class BackpackAssertionDetail(BaseEntityDetailView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializer
    v2_serializer_class = BackpackAssertionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, VerifiedEmailMatchesRecipientIdentifier)
    http_method_names = ('get', 'delete')

    def get(self, request, **kwargs):
        return super(BackpackAssertionDetail, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        obj.acceptance = BadgeInstance.ACCEPTANCE_REJECTED
        obj.save()
        return Response(status=HTTP_200_OK)


class BackpackAssertionDetailImage(ImagePropertyDetailView):
    model = BadgeInstance
    prop = 'image'


class BackpackCollectionList(BaseEntityListView):
    model = BackpackCollection
    v1_serializer_class = CollectionSerializer
    v2_serializer_class = BackpackCollectionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, AuditedModelOwner)

    def get_objects(self, request, **kwargs):
        return self.request.user.cached_backpackcollections()

    def get(self, request, **kwargs):
        return super(BackpackCollectionList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(BackpackCollectionList, self).post(request, **kwargs)


class BackpackCollectionDetail(BaseEntityDetailView):
    model = BackpackCollection
    v1_serializer_class = CollectionSerializer
    v2_serializer_class = BackpackCollectionSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, AuditedModelOwner)

    def get(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).get(request, **kwargs)

    def put(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        return super(BackpackCollectionDetail, self).delete(request, **kwargs)


class BackpackImportBadge(BaseEntityListView):
    v2_serializer_class = BackpackImportSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ('post',)

    def post(self, request, **kwargs):
        return super(BackpackImportBadge, self).post(request, **kwargs)

