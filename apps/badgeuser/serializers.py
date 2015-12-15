from django.conf import settings

from rest_framework import serializers
from rest_framework.authtoken.models import Token

#from earner.serializers import EarnerBadgeSerializer
#from consumer.serializers import ConsumerBadgeDetailSerializer

from .models import BadgeUser


class VerifiedEmailsField(serializers.Field):
    def to_representation(self, obj):
        addresses = []
        for emailaddress in obj.all():
            addresses.append(emailaddress.email)
        return addresses


class UserProfileField(serializers.Serializer):
    """
    Receives the entire BadgeUser instance and returns a dict
    with profile information
    """
    def to_representation(self, obj):
        addresses = []
        if hasattr(obj, 'cached_email'):
            # BadgeUser
            for emailaddress in obj.cached_emails():
                addresses.append(emailaddress.email)
        elif hasattr(obj, 'email'):
            # AnonymousLtiUser
            addresses = [obj.email]
        elif obj.id is None:
            # AnonymousUser
            return {
                'name': "anonymous",
                'username': "",
                'earnerIds': [],
            }

        profile = {
            'name': obj.get_full_name(),
            'username': obj.username,
            'earnerIds': addresses
        }

        if self.context.get('include_token', False):
            profile['token'] = obj.cached_token()

        if getattr(settings, 'BADGR_APPROVED_ISSUERS_ONLY', False):
            profile['approvedIssuer'] = obj.has_perm('issuer.add_issuer')
        else:
            profile['approvedIssuer'] = True

        return profile


class BadgeUserSerializer(serializers.ModelSerializer):
    """
    The BadgeUserSerializer brings together the necessary context information about
    a user's roles as Issuer, Earner, and Consumer
    """
    class Meta:
        model = BadgeUser
        fields = ('userProfile',)

    userProfile = UserProfileField(source='*', read_only=True)
    # earnerBadges = EarnerBadgeSerializer(many=True, read_only=True, source='earnerbadge_set')
    # consumerBadges = ConsumerBadgeDetailSerializer(many=True, read_only=True, source='consumerbadge_set')
    # issuerRoles
