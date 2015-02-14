from rest_framework import serializers

# from rest_framework.exceptions import ValidationError
# from models import BadgeUser
# from badgeanalysis.validation_messages import BadgeValidationError
# from badgeanalysis.models import OpenBadge
from badgeuser.models import BadgeUser
from earner.serializers import EarnerBadgeSerializer


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
        for emailaddress in obj.emailaddress_set.all():
            addresses.append(emailaddress.email)

        profile = {
            'id': obj.id,
            'name': obj.name,
            'username': obj.username,
            'earnerIds': addresses
        }
        return profile


class BadgeUserSerializer(serializers.ModelSerializer):
    """
    The BadgeUserSerializer brings together the necessary context information about
    a user's roles as Issuer, Earner, and Consumer
    """
    class Meta:
        model = BadgeUser
        fields = ('userProfile', 'earnerBadges')

    userProfile = UserProfileField(source='*', read_only=True)
    earnerBadges = EarnerBadgeSerializer(many=True, read_only=True, source='earnerbadge_set')
