from rest_framework import serializers, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from badgeuser.models import CachedEmailAddress
from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import Issuer, IssuerStaff
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing import tsob
from signing.models import SymmetricKey, PublicKey, PrivateKey
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
        if any([staff.is_signer for staff in IssuerStaff.objects.filter(issuer=issuer)]):
            raise ValidationError("Cannot have multiple signers for one issuer")
        new_signer_matching_email = [email for email in CachedEmailAddress.objects.filter(email=request.data['new_signer_email'], verified=True) if email.user.has_surf_conext_social_account()]
        if not new_signer_matching_email:
            raise ValidationError('No matching email found')
        if len(new_signer_matching_email) > 1:
            raise ValidationError('Multiple matching emails found')
        new_signer = new_signer_matching_email[0].user
        staff_instance = IssuerStaff.objects.get(
            user=new_signer,
            issuer=issuer,
        )
        staff_instance.is_signer = True
        staff_instance.save()
        return Response({}, status=status.HTTP_200_OK)


class ChangeIssuerSignerView(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions, OwnsSymmetricKey)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        issuer = Issuer.objects.get(entity_id=request.data['issuer_slug'])
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

        previous_signer_staff_instance = IssuerStaff.objects.get(
            user=old_signer,
            issuer=issuer
        )
        new_signer_staff_instance = IssuerStaff.objects.get(
            user=new_signer,
            issuer=issuer
        )
        if not new_signer_staff_instance.may_become_signer:
            raise ValidationError("Staff member may not become signer, has he or she set a YubiKey password?")

        issuer_signers = [staff for staff in IssuerStaff.objects.filter(issuer=issuer) if staff.is_signer]
        if previous_signer_staff_instance != issuer_signers[0] or len(issuer_signers) > 1:
            raise ValidationError("Cannot have multiple signers for one issuer")
        private_keys_to_reencrypt = list(PrivateKey.objects.filter(symmetric_key=old_signer_symkey, public_key__issuer=issuer))
        if private_keys_to_reencrypt:
            tsob.re_encrypt_private_keys(old_symmetric_key=old_signer_symkey,
                                         new_symmetric_key=new_signer_symkey,
                                         old_password=old_signer_password,
                                         new_password=new_signer_password,
                                         private_key_list=private_keys_to_reencrypt
                                         )
        previous_signer_staff_instance.is_signer = False
        new_signer_staff_instance.is_signer = True
        previous_signer_staff_instance.save()
        new_signer_staff_instance.save()

        return Response({}, status=status.HTTP_200_OK)


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
