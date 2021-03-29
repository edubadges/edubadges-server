from django.db import IntegrityError, transaction
from rest_framework import serializers

from directaward.models import DirectAward, DirectAwardBundle
from issuer.serializers import BadgeClassSlugRelatedField
from mainsite.exceptions import BadgrValidationError


class DirectAwardSerializer(serializers.Serializer):

    class Meta:
        model = DirectAward

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    eppn = serializers.CharField(required=False)
    recipient_email = serializers.EmailField(required=False)

    def create(self, validated_data):
        user_permissions = validated_data['badgeclass'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            direct_award = DirectAward.objects.create(**validated_data)
            direct_award.notify_recipient()
            return direct_award
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance


class DirectAwardBundleSerializer(serializers.Serializer):

    class Meta:
        DirectAwardBundle

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    direct_awards = DirectAwardSerializer(many=True, write_only=True)

    def create(self, validated_data):
        badgeclass = validated_data['badgeclass']
        user_permissions = badgeclass.get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            successfull_direct_awards = []
            try:
                with transaction.atomic():
                    direct_award_bundle = DirectAwardBundle.objects.create(badgeclass=badgeclass,
                                                                           initial_total=validated_data['direct_awards'].__len__())
                    for direct_award in validated_data['direct_awards']:
                        successfull_direct_awards.append(
                            DirectAward.objects.create(bundle=direct_award_bundle,
                                                       badgeclass=badgeclass,
                                                       **direct_award)
                        )
            except IntegrityError:
                raise BadgrValidationError("A direct award already exists with this eppn for this badgeclass", 999)
            direct_award_bundle.notify_recipients()
            return direct_award_bundle
        raise BadgrValidationError("You don't have the necessary permissions", 100)
