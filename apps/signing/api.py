from rest_framework import serializers, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from badgeuser.models import CachedEmailAddress
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import Issuer
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing import tsob
from signing.models import SymmetricKey, PublicKey
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


class ChangeIssuerSignerView(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions, OwnsSymmetricKey)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        old_signer_password = request.data['old_signer_password']
        new_signer_password = request.data['new_signer_password']
        old_signer_matching_email = [email for email in CachedEmailAddress.objects.filter(email=request.data['old_signer_email'], verified=True) if email.user.has_surf_conext_social_account()]
        new_signer_matching_email = [email for email in CachedEmailAddress.objects.filter(email=request.data['new_signer_email'], verified=True) if email.user.has_surf_conext_social_account()]
        if not old_signer_matching_email or not new_signer_matching_email:
            raise CachedEmailAddress.DoesNotExist
        old_signer = old_signer_matching_email[0].user
        new_signer = new_signer_matching_email[0].user
        old_signer_symkey = SymmetricKey.objects.get(user=old_signer, current=True)
        new_signer_symkey = SymmetricKey.objects.get(user=new_signer, current=True)
        try:
            old_signer_symkey.validate_password(old_signer_password)
            new_signer_symkey.validate_password(new_signer_password)
        except ValueError as e:
            return Response("Wrong password entered", status=status.HTTP_400_BAD_REQUEST)
        tsob.re_encrypt_private_keys(old_signer_symkey,
                                     new_signer_symkey,
                                     old_signer_password,
                                     new_signer_password)
        return Response({'valid': True}, status=status.HTTP_200_OK)


class PublicKeyDetailView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['get']
    model = PublicKey

    def get(self, request, **kwargs):
        pubkey = PublicKey.objects.get(entity_id=kwargs['entity_id'])
        return Response(
            {
                "@context": "https://w3id.org/openbadges/v2",
                "type": "CryptographicKey",
                "id": pubkey.public_url,
                "owner": pubkey.issuer.public_url,
                "publicKeyPem": pubkey.public_key_pem
            }
        )
