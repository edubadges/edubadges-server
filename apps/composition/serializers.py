import os
import uuid

from rest_framework import serializers

from mainsite.logs import badgr_log
from verifier import ComponentsSerializer
from verifier.utils import (domain, find_and_get_badge_class,
                            find_and_get_issuer)

from .format import V1InstanceSerializer
from .models import (LocalBadgeInstance, LocalBadgeClass, LocalIssuer,
                     Collection, LocalBadgeInstanceCollection)
from .utils import (get_verified_badge_instance_from_form,
                    badge_email_matches_emails,
                    use_or_bake_badge_instance_image)

class LocalBadgeInstanceUploadSerializer(serializers.Serializer):
    # Form submission fields as populated by request.data in the API
    image = serializers.ImageField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    assertion = serializers.CharField(required=False, write_only=True)

    # Reinstantiation using fields from badge instance when returned by .create
    id = serializers.IntegerField(read_only=True)
    json = V1InstanceSerializer(read_only=True)

    def to_representation(self, obj):
        """
        If the APIView initialized the serializer with the extra context
        variable 'format' from a query param in the GET request with the
        value "plain", make the `json` field for this instance read_only.
        """
        if self.context.get('format', 'v1') == 'plain':
            self.fields.json = serializers.DictField(read_only=True)
        return super(LocalBadgeInstanceUploadSerializer, self) \
            .to_representation(obj)

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

        # Fetch payload and instance id (url) from one of many types of input
        badge_instance_url, badge_instance = \
            get_verified_badge_instance_from_form(validated_data)
        try:
            _, badge_class = find_and_get_badge_class(badge_instance['badge'])
            _, issuer = find_and_get_issuer(badge_class['issuer'])
        except KeyError as e:
            raise serializers.ValidationError(
                "Badge components not well formed. Missing structure: {}"
                .format(e.message))

        components = ComponentsSerializer(badge_instance, badge_class, issuer)

        if not components.is_valid():
            raise serializers.ValidationError(
                "The uploaded badge did not validate.")

        # Non form-specific validation (Validation between components)
        components.validate(raise_exception=True)

        # Form-specific badge instance validation (reliance on URL input)
        if components.badge_instance.version.startswith('v0.5'):
            if not validated_data.get('url'):
                raise serializers.ValidationError(
                    "We cannot verify a v0.5 badge without its hosted URL.")

        # Form-specific context information passed to Serializer (URL input)
        # TODO: Pass this in context not via a ComponentsSerializer attribute
        if components.issuer.version.startswith('v0.5'):
            components.badge_instance_url = validated_data['url']
        if components.issuer.version.startswith('v1'):
            if badge_instance['verify']['type'] == 'hosted':
                components.badge_instance_url = badge_instance['verify']['url']

        # Form-specific badge instance validation (reliance on form data)
        if components.issuer.version.startswith('v0.5'):
            if not (domain(components.issuer['origin']) ==
                    domain(validated_data['url'])):
                raise serializers.ValidationError(
                    "We cannot verify a v0.5 badge without its hosted URL.")

        # Request.user specific validation
        verified_emails = request_user.emailaddress_set.all()
        matched_email = badge_email_matches_emails(badge_instance,
                                                   verified_emails)
        if not matched_email:
            raise serializers.ValidationError(
                "The badge you are trying to import does not belong to one of \
                your verified e-mail addresses.")
        # TODO: Pass this in context not via a ComponentsSerializer attribute
        components.recipient_id = matched_email


        # Create local component instance `json` fields
        badge_instance_json = \
            components.badge_instance.serializer(badge_instance, context={
                'instance_url': badge_instance_url,  # To populate BI id
                'recipient_id': badge_check.matched_email,  # For 0.5 badges
                # A BadgeInstanceSerializer will recursively instantiate
                # serializers of the other components to nest a representation
                # of their .data for BI['badge'] and BI['badge']['issuer']
                'badge_class': badge_class,  # To instantiate the BC Serializer
                'issuer': issuer}).data  # To instantiate the Issuer Serializer

        # Create local component instances
        new_issuer = LocalIssuer.objects.create(**{
            'name': issuer['name'],
            'json': badge_instance_json['badge']['issuer'],
        })

        new_badge_class = LocalBadgeClass.objects.create(**{
            'name': badge_class['name'],
            'json': badge_instance_json['badge'],
            'issuer': new_issuer,
        })

        new_instance = LocalBadgeInstance.objects.create(**{
            'recipient_user': request_user,
            'json': badge_instance_json,
            'badgeclass': new_badge_class,
            'issuer': new_issuer,
            'email': matched_email,
            'image': use_or_bake_badge_instance_image(
                validated_data.get('image'), badge_instance, badge_class)
        })
        new_instance.json['image'] = new_instance.image_url()
        new_instance.save()

        return new_instance


class CollectionLocalBadgeInstanceListSerializer(serializers.ListSerializer):

    def create(self, validated_data):
        collection = self.context.get('collection')
        request_user = self.context.get('request').user

        if not isinstance(validated_data, list):
            validated_data = [validated_data]

        id_set = [x.get('instance', {}).get('id') for x in validated_data]

        badge_set = LocalBadgeInstance.objects.filter(
            recipient_user=request_user, id__in=id_set
        ).exclude(collection=collection)

        new_records = []

        for badge in badge_set:
            description = [
                item for item in validated_data if
                item.get('instance', {}).get('id') == badge.id
            ][0].get('description', '')

            new_records.append(LocalBadgeInstanceCollection(
                instance=badge,
                collection=collection,
                description=description
            ))

        if len(new_records) > 0:
            return LocalBadgeInstanceCollection.objects.bulk_create(new_records)
        else:
            return new_records


class CollectionLocalBadgeInstanceSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True, source='instance.id')
    description = serializers.CharField(required=False)

    class Meta:
        list_serializer_class = CollectionLocalBadgeInstanceListSerializer

    def create(self, validated_data):
        collection = self.context.get('collection')
        request_user = self.context.get('request').user

        badge_query = LocalBadgeInstance.objects.filter(
            recipient_user=request_user,
            id=validated_data.get('instance', {}).get('id'),
        ).exclude(collection=collection)

        if not badge_query.exists():
            return []

        description = validated_data.get('description', '')

        new_record = LocalBadgeInstanceCollection(
            instance=badge_query[0], collection=collection,
            description=description
        )

        new_record.save()
        return new_record


class CollectionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128)
    slug = serializers.CharField(required=False, max_length=128)
    description = serializers.CharField(required=False, max_length=255)
    share_hash = serializers.CharField(required=False, max_length=255)
    share_url = serializers.CharField(read_only=True, max_length=1024)
    badges = serializers.ListField(
        required=False, child=CollectionLocalBadgeInstanceSerializer(),
        source='localbadgeinstancecollection_set.all')

    def create(self, validated_data):
        user = self.context.get('request').user

        new_collection = Collection(
            name=validated_data.get('name'),
            slug=validated_data.get('slug', None),
            description=validated_data.get('description', ''),
            owner=user)

        if validated_data.get('badges') is not None:
            raise NotImplementedError(
                "Adding badges to collection on creation not implemented.")

        new_collection.save()
        return new_collection
