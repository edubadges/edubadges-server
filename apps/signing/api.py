from rest_framework import serializers

from entity.api import BaseEntityListView, BaseEntityDetailView
from signing.models import SymmetricKey
from signing.permissions import MaySignAssertions, OwnsSymmetricKey
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing.serializers import SymmetricKeySerializer


class SymmetricKeyListView(BaseEntityListView):
    model = SymmetricKey
    http_method_names = ['post']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions, OwnsSymmetricKey)
    serializer_class = SymmetricKeySerializer
    serializer_class_v1 = SymmetricKeySerializer

    def post(self, request, **kwargs):
        """
        Add password to create a SymmetricKey for this user
        """
        password = request.data.get('password', None)
        if not password:
            raise serializers.ValidationError({"password": "field is required"})
        return super(SymmetricKeyListView, self).post(request, **kwargs)

    def get(self, request, **kwargs):
        return super(SymmetricKeyListView, self).get(request, **kwargs)

    def get_objects(self, request, **kwargs):
        return SymmetricKey.objects.filter(user=request.user, current=True)


class SymmetricKeyDetailView(BaseEntityDetailView):
    model = SymmetricKey
    http_method_names = ['put', 'get']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions, OwnsSymmetricKey)
    serializer_class = SymmetricKeySerializer

    def get_object(self, request, **kwargs):
        return SymmetricKey.objects.filter(user=request.user, current=True).first()

