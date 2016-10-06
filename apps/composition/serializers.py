from collections import OrderedDict

from django.core.urlresolvers import reverse
from rest_framework import serializers

import badgrlog
from badgeuser.models import EmailAddressVariant
from issuer.models import BadgeInstance
from mainsite.drf_fields import Base64FileField
from mainsite.utils import OriginSetting
from verifier import ComponentsSerializer
from verifier.badge_check import BadgeCheck
from verifier.utils import find_and_get_badge_class, find_and_get_issuer

from .format import V1InstanceSerializer, V1BadgeInstanceSerializer
from .models import (LocalBadgeInstance, LocalBadgeClass, LocalIssuer,
                     Collection, LocalBadgeInstanceCollection)
from .utils import (get_verified_badge_instance_from_form,
                    use_or_bake_badge_instance_image, get_badge_by_identifier)

logger = badgrlog.BadgrLogger()


class LocalBadgeInstanceUploadSerializer(serializers.Serializer):
    # Form submission fields as populated by request.data in the API
    image = Base64FileField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    assertion = serializers.CharField(required=False, write_only=True)
    recipient_id = serializers.CharField(required=False, write_only=True)

    # Reinstantiation using fields from badge instance when returned by .create
    id = serializers.IntegerField(read_only=True)
    # json = V1InstanceSerializer(read_only=True)

    def to_representation(self, obj):
        """
        If the APIView initialized the serializer with the extra context
        variable 'format' from a query param in the GET request with the
        value "plain", make the `json` field for this instance read_only.
        """
        if self.context.get('format', 'v1') == 'plain':
            self.fields.json = serializers.DictField(read_only=True)
        representation = super(LocalBadgeInstanceUploadSerializer, self).to_representation(obj)

        if isinstance(obj, LocalBadgeInstance):
            representation['json'] = V1InstanceSerializer(obj.json, context=self.context).data
        elif isinstance(obj, BadgeInstance):
            representation['id'] = obj.slug
            representation['json'] = V1BadgeInstanceSerializer(obj, context=self.context).data

        representation['shareUrl'] = OriginSetting.HTTP+reverse('shared_badge', kwargs={'badge_id': obj.slug})

        representation['imagePreview'] = {
            "type": "image",
            "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('localbadgeinstance_image', kwargs={'slug': obj.slug}))
        }
        if obj.issuer.image_preview:
            representation['issuerImagePreview'] = {
                "type": "image",
                "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('localissuer_image', kwargs={'slug': obj.issuer.slug}))
            }
        return representation

    def validate_recipient_id(self, data):
        user = self.context.get('request').user
        current_emails = [e.email for e in user.cached_emails()] + [e.email for e in user.cached_email_variants()]

        if data in current_emails:
            return None
        if user.can_add_variant(data):
            return data
        raise serializers.ValidationError("Requested recipient ID {} is not one of your verified email addresses.")

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
        verified_emails = [e.email for e in request_user.emailaddress_set.filter(verified=True)] \
                          + [e.email for e in request_user.cached_email_variants()]
        new_variant = None
        if validated_data.get('recipient_id') and validated_data.get('recipient_id') not in verified_emails:
            new_variant = EmailAddressVariant(email=validated_data['recipient_id'])
            verified_emails.append(new_variant.email)

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

        if new_variant and badge_check.recipient_id == new_variant.email:
            new_variant.save()

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

        existing_instance = BadgeInstance.objects.filter(slug=badge_instance_json.get('uid')).first()
        if existing_instance:
            if existing_instance.acceptance == BadgeInstance.ACCEPTANCE_REJECTED:
                existing_instance.acceptance = BadgeInstance.ACCEPTANCE_ACCEPTED
                existing_instance.save()
                logger.event(badgrlog.BadgeUploaded(badge_instance_json, badge_check, request_user))
                return existing_instance
            else:
                raise serializers.ValidationError("This badge has already been uploaded.")

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


class CollectionBadgesSerializer(serializers.ListSerializer):

    def save(self, **kwargs):
        collection = self.context.get('collection')
        updated_ids = set()

        # get all referenced badges in validated_data
        for entry in self.validated_data:
            if not entry.pk or getattr(entry, '_dirty', False):
                entry.save()
            updated_ids.add(entry.pk)

        if not self.context.get('add_only', False):
            for old_entry in collection.badges.all():
                if old_entry.pk not in updated_ids:
                    old_entry.delete()

        self.instance = self.validated_data
        # return a list of the new entries added (which is all of the final list in case of update)
        return [e for e in self.validated_data if e.pk in updated_ids]


class CollectionBadgeSerializer(serializers.ModelSerializer):
    id = serializers.RelatedField(queryset=LocalBadgeInstance.objects.all())
    collection = serializers.RelatedField(queryset=Collection.objects.all(), write_only=True, required=False)

    class Meta:
        model = LocalBadgeInstanceCollection
        list_serializer_class = CollectionBadgesSerializer
        fields = ('id', 'description', 'instance', 'collection')

    def get_validators(self):
        return []

    def to_internal_value(self, data):
        description = data.get('description', '') or ''

        # populate collection from various methods
        collection = data.get('collection')
        if not collection:
            collection = self.context.get('collection')
        if not collection and self.parent.parent:
            collection = self.parent.parent.instance
        elif not collection and self.parent.instance:
            collection = self.parent.instance
        if not collection:
            return LocalBadgeInstanceCollection(
                instance_id=data.get('id'), description=description)

        badge = get_badge_by_identifier(data.get('id'))
        get_kwargs = {
            'collection': collection
        }
        if isinstance(badge, LocalBadgeInstance):
            get_kwargs['issuer_instance__isnull'] = True
            get_kwargs['instance_id'] = badge.pk
        elif isinstance(badge, BadgeInstance):
            get_kwargs['issuer_instance_id'] = badge.pk
            get_kwargs['instance__isnull'] = True

        try:
            instance = LocalBadgeInstanceCollection.objects.get(**get_kwargs)

            if description != instance.description:
                instance.description = description
                instance._dirty = True  # record if instance needs to be updated in list serializer

        except LocalBadgeInstanceCollection.DoesNotExist:
            instance = LocalBadgeInstanceCollection(
                collection=collection,
                description=description
            )
            if isinstance(badge, LocalBadgeInstance):
                instance.instance_id = badge.pk
            elif isinstance(badge, BadgeInstance):
                instance.issuer_instance_id = badge.pk

            if instance.collection.owner != instance.badge_instance.recipient_user:
                raise serializers.ValidationError(
                    "Cannot add badge to a collection created by a different recipient.")

        return instance

    def to_representation(self, instance):
        ret = OrderedDict()
        ret['id'] = instance.badge_id
        ret['description'] = instance.description
        return ret


class CollectionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128)
    slug = serializers.CharField(required=False, max_length=128)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    share_hash = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=255)
    share_url = serializers.CharField(read_only=True, max_length=1024)
    badges = CollectionBadgeSerializer(
        read_only=False, many=True, required=False
    )
    published = serializers.BooleanField(required=False)

    def create(self, validated_data):
        user = self.context.get('user')

        new_collection = Collection(
            name=validated_data.get('name'),
            slug=validated_data.get('slug', None),
            description=validated_data.get('description', ''),
            owner=user)

        new_collection.published = validated_data.get('published', False)
        new_collection.save()

        if validated_data.get('badges') is not None:
            for entry in validated_data['badges']:
                entry.collection = new_collection
                entry.save()

        return new_collection

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.published = validated_data.get('published', instance.published)

        if 'badges' in validated_data\
                and validated_data['badges'] is not None:

            existing_entries = list(instance.badges.all())
            updated_ids = set()

            for entry in validated_data['badges']:
                if not entry.pk:
                    entry.save()
                updated_ids.add(entry.pk)

            for old_entry in existing_entries:
                if old_entry.pk not in updated_ids:
                    old_entry.delete()

        instance.save()
        return instance
