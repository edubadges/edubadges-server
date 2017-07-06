from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.models import SocialAccount
from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT, HTTP_403_FORBIDDEN

from badgrsocialauth.permissions import IsSocialAccountOwner
from badgrsocialauth.serializers import BadgrSocialAccountSerializerV1
from entity.api import BaseEntityListView, BaseEntityDetailView
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class BadgrSocialAccountList(BaseEntityListView):
    """
    Issuer list resource for the authenticated user
    """
    model = SocialAccount
    v1_serializer_class = BadgrSocialAccountSerializerV1
    v2_serializer_class = BadgrSocialAccountSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    def get_objects(self, request, **kwargs):
        obj =  self.request.user.socialaccount_set.all()
        return obj

    def get(self, request, **kwargs):
        return super(BadgrSocialAccountList, self).get(request, **kwargs)


class BadgrSocialAccountDetail(BaseEntityDetailView):
    model = SocialAccount
    v1_serializer_class = BadgrSocialAccountSerializerV1
    v2_serializer_class = BadgrSocialAccountSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, IsSocialAccountOwner)

    def get_object(self, request, **kwargs):
        try:
            return SocialAccount.objects.get(id=kwargs.get('id'))
        except SocialAccount.DoesNotExist:
            raise Http404

    def get(self, request, **kwargs):
        return super(BadgrSocialAccountDetail, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        social_account = self.get_object(request, **kwargs)

        if not self.has_object_permissions(request, social_account):
            return Response(status=HTTP_404_NOT_FOUND)

        try:
            user_social_accounts = SocialAccount.objects.filter(user=request.user)
            get_adapter().validate_disconnect(social_account, user_social_accounts)
        except ValidationError:
            return Response(status=HTTP_403_FORBIDDEN)

        social_account.delete()

        return Response(status=HTTP_204_NO_CONTENT)