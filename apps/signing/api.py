from rest_framework import serializers, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from badgeuser.models import CachedEmailAddress
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import Issuer, IssuerStaff
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing.models import SymmetricKey, PublicKeyIssuer
from signing.permissions import MaySignAssertions, OwnsSymmetricKey
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


class SetIssuerSignerView(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions, OwnsSymmetricKey)
    http_method_names = ['put']

    def put(self, request, **kwargs):
        issuer = Issuer.objects.get(entity_id=request.data['issuer_slug'])
        remove = request.data.get('action') == 'remove'
        add = request.data.get('action') == 'add'
        signer_matching_email = [email for email in CachedEmailAddress.objects.filter(email=request.data['signer_email'], verified=True) if email.user.has_surf_conext_social_account()]
        if not signer_matching_email:
            raise ValidationError('No matching email found')
        if len(signer_matching_email) > 1:
            raise ValidationError('Multiple matching emails found')
        signer = signer_matching_email[0].user
        staff_instance = IssuerStaff.objects.get(
            user=signer,
            issuer=issuer,
        )
        if add:
            staff_instance.is_signer = True
        if remove:
            staff_instance.is_signer = False
        staff_instance.save()
        return Response({}, status=status.HTTP_200_OK)


class PublicKeyIssuerDetailView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['get']
    model = PublicKeyIssuer

    def get(self, request, **kwargs):
        pubkey_issuer = PublicKeyIssuer.objects.get(entity_id=kwargs['entity_id'])
        return Response(
            {
                "@context": "https://w3id.org/openbadges/v2",
                "type": "CryptographicKey",
                "id": pubkey_issuer.public_url,
                "owner": pubkey_issuer.owner_public_url,
                "publicKeyPem": pubkey_issuer.public_key.public_key_pem
            }
        )
