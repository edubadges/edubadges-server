from collections import OrderedDict

from rest_framework import serializers

from .fields import (BadgeStringField, BadgeURLField, BadgeImageURLField,
                     BadgeEmailField)
from ..utils import ObjectView

class IssuerSerializerV0_5(serializers.Serializer):
    """
    A representation of a badge's issuing organization is found embedded in
    0.5 badge assertions.
    """
    origin = serializers.URLField(required=True)
    name = serializers.CharField(required=True)
    org = serializers.CharField(required=False)
    contact = serializers.EmailField(required=False)


class IssuerSerializerV1_0(serializers.Serializer):
    name = BadgeStringField(required=True)
    url = BadgeURLField(required=True)
    description = BadgeStringField(required=False)
    email = BadgeEmailField(required=False)
    image = BadgeImageURLField(required=False)
    revocationList = BadgeURLField(required=False)

    def to_representation(self, badge):
        obj = ObjectView(dict(badge))
        issuer_props = super(
            IssuerSerializerV1_0, self).to_representation(obj)
        
        header = OrderedDict()
        if not self.context.get('embedded', False):
            header['@context'] = 'https://w3id.org/openbadges/v1'
        header['type'] = 'Issuer'
        header['id'] = self.context.get('instance').issuer_url

        result = OrderedDict(header.items() + issuer_props.items())

        return result