from rest_framework import serializers

from entity.api import BaseEntityListView
from signing.models import SymmetricKey
from signing.permissions import MaySignAssertions
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing.serializers import SymmetricKeySerializer

class SymmetricKeyView(BaseEntityListView):
    model = SymmetricKey
    http_method_names = ['get', 'post']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)
    serializer_class = SymmetricKeySerializer
    serializer_class_v1 = SymmetricKeySerializer

    def post(self, request, **kwargs):
        """
        Add password to create a SymmetricKey for this user
        """
        password = request.data.get('password', None)
        if not password:
            raise serializers.ValidationError({"password": "field is required"})
        return super(SymmetricKeyView, self).post(request, **kwargs)

    def get_objects(self, request, **kwargs):
        return SymmetricKey.objects.filter(user=request.user, current=True)
