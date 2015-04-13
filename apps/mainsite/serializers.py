import json

from django.conf import settings
from django.db.models import Q

from rest_framework import serializers


class ReadOnlyJSONField(serializers.CharField):

    def to_representation(self, value):
        if isinstance(value, (dict, list)):
            return value
        else:
            raise serializers.ValidationError("WriteableJsonField: Did not get a JSON-serializable datatype from storage for this item: " + str(value))


class WritableJSONField(ReadOnlyJSONField):
    def to_internal_value(self, data):
        try:
            internal_value = json.loads(data)
        except Exception:
            # TODO: this is going to choke on dict input, when it should be allowed in addition to JSON.
            raise serializers.ValidationError("WriteableJsonField: Could not process input into a python dict for storage " + str(data))

        return internal_value


class UserViewDataSerializer(serializers.Serializer):
    """
    A serializer used to pass initial data to a view template so that the React.js
    front end can render.
    It should detect which of the core Badgr applications are installed and return
    appropriate contextual information.
    """

    def to_representation(self, user):
        view_data = {}

        if 'issuer' in settings.BADGR_INSTALLED_APPS:
            from issuer.models import Issuer
            from issuer.serializers import IssuerSerializer
            user_issuers = Issuer.objects.filter(
                Q(owner__id=user.id) |
                Q(staff__id=user.id)
            ).select_related('badgeclasses')

            issuer_context = self.context.copy()
            issuer_context['embed_badgeclasses'] = True
            issuer_data = IssuerSerializer(
                user_issuers,
                many=True,
                context=issuer_context
            )
            view_data['issuer'] = issuer_data.data

        if 'badgeuser' in settings.BADGR_INSTALLED_APPS:
            from badgeuser.models import BadgeUser
            from badgeuser.serializers import UserProfileField
            view_data['user'] = UserProfileField(user, context=self.context).data

        return view_data
