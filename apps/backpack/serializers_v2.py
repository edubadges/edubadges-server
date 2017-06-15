# encoding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as RestframeworkValidationError

from backpack.models import BackpackCollection
from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2
from issuer.helpers import BadgeCheckHelper
from issuer.models import BadgeInstance, BadgeClass
from issuer.serializers_v2 import BadgeRecipientSerializerV2, EvidenceItemSerializerV2
from mainsite.drf_fields import ValidImageField
from mainsite.serializers import MarkdownCharField, HumanReadableBooleanField


class BackpackAssertionSerializerV2(DetailSerializerV2):
    acceptance = serializers.ChoiceField(choices=BadgeInstance.ACCEPTANCE_CHOICES, default=BadgeInstance.ACCEPTANCE_ACCEPTED)

    # badgeinstance
    openBadgeId = serializers.URLField(source='source_url', read_only=True)
    badgeclass = EntityRelatedFieldV2(source='cached_badgeclass', required=False, queryset=BadgeClass.cached)
    image = serializers.FileField(read_only=True)
    recipient = BadgeRecipientSerializerV2(source='*')
    # issuedOn = serializers.DateTimeField(source='created_at', read_only=True)
    narrative = MarkdownCharField(required=False)
    evidence = EvidenceItemSerializerV2(many=True, required=False)
    revoked = HumanReadableBooleanField(read_only=True)
    revocationReason = serializers.CharField(source='revocation_reason', read_only=True)

    class Meta(DetailSerializerV2.Meta):
        model = BadgeInstance


class BackpackCollectionSerializerV2(DetailSerializerV2):
    name = serializers.CharField()
    description = MarkdownCharField(required=False)
    share_url = serializers.URLField(read_only=True)
    published = serializers.BooleanField(required=False)

    assertions = EntityRelatedFieldV2(many=True, source='badge_items', required=False, queryset=BadgeInstance.cached)

    class Meta(DetailSerializerV2.Meta):
        model = BackpackCollection


class BackpackImportSerializerV2(DetailSerializerV2):
    url = serializers.URLField(required=False)
    image = ValidImageField(required=False)
    assertion = serializers.DictField(required=False)

    def validate(self, attrs):
        if sum(1 if v else 0 for v in attrs.values()) != 1:
            raise serializers.ValidationError("Must provide only one of 'url', 'image' or 'assertion'.")
        return attrs

    def create(self, validated_data):
        try:
            instance, created = BadgeCheckHelper.get_or_create_assertion(**validated_data)
        except DjangoValidationError as e:
            raise RestframeworkValidationError(e.messages)
        return instance

