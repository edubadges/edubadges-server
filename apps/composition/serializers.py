from django.core.urlresolvers import reverse
from rest_framework import serializers

import badgrlog
from mainsite.drf_fields import Base64FileField
from mainsite.utils import OriginSetting
from verifier import ComponentsSerializer
from verifier.badge_check import BadgeCheck
from verifier.utils import find_and_get_badge_class, find_and_get_issuer

from .format import V1InstanceSerializer
from .models import (LocalBadgeInstance, LocalBadgeClass, LocalIssuer,
                     Collection, LocalBadgeInstanceCollection)
from .utils import (get_verified_badge_instance_from_form,
                    use_or_bake_badge_instance_image)

logger = badgrlog.BadgrLogger()


class LocalBadgeInstanceUploadSerializer(serializers.Serializer):
    # Form submission fields as populated by request.data in the API
    image = Base64FileField(required=False, write_only=True)
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
        representation = super(LocalBadgeInstanceUploadSerializer, self).to_representation(obj)
        representation['imagePreview'] = {
            "type": "image",
            "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('localbadgeinstance_image', kwargs={'slug': obj.slug}))
        }
        if obj.issuer.image_preview :
            representation['issuerImagePreview'] = {
                "type": "image",
                "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('localissuer_image', kwargs={'slug': obj.issuer.slug}))
            }
        return representation

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
            badge_class_url, badge_class = \
                find_and_get_badge_class(badge_instance['badge'])
            issuer_url, issuer = find_and_get_issuer(badge_class['issuer'])
        except KeyError as e:
            raise serializers.ValidationError(
                "Badge components not well formed. Missing structure: {}"
                .format(e.message))

        # Find and assign a Serializer to each badge Component
        components = ComponentsSerializer(badge_instance, badge_class, issuer)
        if not components.is_valid():
            error = {
                'message': "The uploaded badge did not validate.",
                 'details': {
                     'instance': components.badge_instance.version_errors,
                     'badge_class': components.badge_class.version_errors,
                     'issuer': components.issuer.version_errors
                 }
            }
            logger.event(badgrlog.InvalidBadgeUploaded(components, error, request_user))
            raise serializers.ValidationError(error)

        # Check non-structural business logic checks and constraints
        verified_emails = request_user.emailaddress_set.filter(verified=True) \
            .values_list('email', flat=True)
        badge_check = BadgeCheck(
            components.badge_instance, components.badge_class,
            components.issuer, verified_emails, badge_instance_url)
        badge_check.validate()

        if not badge_check.is_valid():
            error = {
                'message':
                "The uploaded badge did not pass verification constraints.",
                'detail':
                [error['message'] for error in badge_check.results
                 if error['type'] is 'error' and not error['success']]
            }
            logger.event(badgrlog.InvalidBadgeUploaded(components, error, request_user))
            raise serializers.ValidationError(error)

        # Don't support v0.5 badges until solution reached on nested components
        if components.badge_instance.version.startswith('v0'):
            error = "Sorry, v0.5 badges are not supported at this time. This \
badge was valid, but cannot be saved."
            logger.event(badgrlog.InvalidBadgeUploaded(components, error, request_user))
            raise serializers.ValidationError(error)

        # Create local component instance `json` fields
        badge_instance_json = \
            components.badge_instance.serializer(badge_instance, context={
                'instance_url': badge_instance_url,  # To populate BI id
                'recipient_id': badge_check.recipient_id,  # For 0.5 badges
                # A BadgeInstanceSerializer will recursively instantiate
                # serializers of the other components to nest a representation
                # of their .data for BI['badge'] and BI['badge']['issuer']
                'badge_class': badge_class,  # To instantiate the BC Serializer
                'issuer': issuer}).data  # To instantiate the Issuer Serializer

        # Create local component instances
        if issuer_url and badge_class_url:
            non_embedded_issuer_json = components.issuer.serializer(
                issuer, context={'issuer_id': issuer_url}).data
            new_issuer, _ = LocalIssuer.objects.get_or_create({
                'name': issuer['name'],
                'json': non_embedded_issuer_json
            }, identifier=issuer_url)

            non_embedded_badge_class_json = \
                components.badge_class.serializer(
                    badge_class, context={'badge_class_id': badge_class_url,
                                          'issuer': issuer,
                                          'issuer_id': issuer_url}).data
            new_badge_class, _ = LocalBadgeClass.objects.get_or_create({
                'name': badge_class['name'],
                'json': non_embedded_badge_class_json,
                'issuer': new_issuer,
            }, identifier=badge_class_url)
        else:  # 0.5 badges
            new_issuer, new_badge_class = None, None

        new_instance, instance_created = LocalBadgeInstance.objects.get_or_create({
            'recipient_user': request_user,
            'json': badge_instance_json,
            'badgeclass': new_badge_class,
            'issuer': new_issuer,
            'recipient_identifier': badge_check.recipient_id,
            'image': use_or_bake_badge_instance_image(
                validated_data.get('image'), badge_instance, badge_class)
        }, identifier=badge_instance_url, recipient_user=request_user)
        # TODO: Prevent saving twice

        if not instance_created:
            raise serializers.ValidationError("This badge has already been uploaded.")

        new_instance.json['image'] = new_instance.image_url()
        new_instance.save()

        logger.event(badgrlog.BadgeUploaded(badge_instance_json, badge_check, request_user))

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
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

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

    def to_internal_value(self, data):
        collection = self.context.get('collection')
        request_user = self.context.get('request').user
        description = data.get('description', "")

        badge = LocalBadgeInstance.objects.get(
            recipient_user=request_user,
            id=data.get('id'),
        )

        entry = None
        try:
            entry = LocalBadgeInstanceCollection.objects.get(
                instance=badge,
                collection=collection
            )
        except LocalBadgeInstanceCollection.DoesNotExist:
            pass

        if not entry:
            entry = LocalBadgeInstanceCollection(
                instance=badge,
                collection=collection
            )

        entry.description = description or ""

        return entry

    def update(self, instance, validated_data):
        instance.id = validated_data.get('id', instance.id)
        instance.description = validated_data.get('description', instance.description) or ""

        instance.save()
        return instance


class CollectionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128)
    slug = serializers.CharField(required=False, max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    share_hash = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    share_url = serializers.CharField(read_only=True, max_length=1024)
    badges = CollectionLocalBadgeInstanceSerializer(
        read_only=False, many=True, required=False, source='localbadgeinstancecollection_set.all'
    )
    published = serializers.BooleanField(write_only=True, required=False)

    def create(self, validated_data):
        user = self.context.get('user')

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

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.published = validated_data.get('published', instance.published)

        if 'localbadgeinstancecollection_set' in validated_data\
                and validated_data['localbadgeinstancecollection_set'] is not None:

            existing_entries = instance.localbadgeinstancecollection_set.all()
            updated_ids = set()

            for entry in validated_data.get('localbadgeinstancecollection_set')['all']:
                updated_ids.add(entry.instance.id)
                entry.save()

            for old_entry in existing_entries:
                if not old_entry.instance.id in updated_ids:
                    old_entry.delete()

        instance.save()
        return instance