import json
from mainsite.logs import badgr_log

from rest_framework import serializers

from verifier import ComponentsSerializer
from verifier.utils import (domain, find_and_get_badge_class,
                            find_and_get_issuer)
from local_components.models import (BadgeInstance as LocalBadgeInstance,
                                     BadgeClass as LocalBadgeClass,
                                     Issuer as LocalIssuer)

from .utils import (get_verified_badge_instance_from_form,
                    badge_email_matches_emails)

#  from .models import Collection, LocalBadgeInstanceCollection


class LocalBadgeInstanceSerializer(serializers.Serializer):
    pass


class LocalBadgeInstanceUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    assertion = serializers.DictField(required=False, write_only=True)

    def validate(self, data):
        """
        Ensure only one assertion input field given.
        """

        fields_present = ['image' in data, 'url' in data,
                          'assertion' in data and data.get('assertion')]
        if (fields_present.count(True) > 1):
            raise serializers.ValidationError(
                "Only one instance input field allowed.")

        return data

    def create(self, validated_data):
        request_user = self.context.get('request').user

        badge_instance = get_verified_badge_instance_from_form(validated_data)
        badge_class = find_and_get_badge_class(badge_instance['badge'])
        issuer = find_and_get_issuer(badge_class['issuer'])

        components = ComponentsSerializer(badge_instance, badge_class, issuer)

        if not components.is_valid():
            raise serializers.ValidationError(
                "The uploaded badge did not validate.")

        # Form-specific badge instance validation (reliance on URL input)
        if components.badge_instance.version.startswith('v0.5'):
            if not validated_data.get('url'):
                raise serializers.ValidationError(
                    "We cannot verify a v0.5 badge without its hosted URL.")

        # Form-specific badge instance validation (reliance on form data)
        if components.issuer.version.startswith('v0.5'):
            if not (domain(components.issuer['origin']) ==
                    domain(validated_data['url'])):
                raise serializers.ValidationError(
                    "We cannot verify a v0.5 badge without its hosted URL.")

        verified_emails = request_user.emailaddress_set.all()
        if not badge_email_matches_emails(badge_instance, verified_emails):
            raise serializers.ValidationError(
                "The badge you are trying to import does not belong to one of \
                your verified e-mail addresses.")

        # Non form-specific validation (Validation between components)
        components.validate(raise_exception=True)

        # * Assign the image
        #   (Can/should the/a serializer do this? LocalBadgeInstanceSerializer)

        new_issuer = LocalIssuer.objects.create(**{
            'name': issuer['name'],
            'json': json.dumps(issuer),
        })

        new_badge_class = LocalBadgeClass.objects.create(**{
            'name': badge_class['name'],
            'json': json.dumps(badge_class),
            'issuer': new_issuer,
        })

        new_instance = LocalBadgeInstance.objects.create(**{
            'json': json.dumps(badge_instance),
            'badgeclass': new_badge_class,
            'issuer': new_issuer,
            'email': request_user.email,
        })

        return new_instance
