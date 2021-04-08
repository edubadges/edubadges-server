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
    status = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance


class DirectAwardBundleSerializer(serializers.Serializer):

    class Meta:
        DirectAwardBundle

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    direct_awards = DirectAwardSerializer(many=True, write_only=True)
    entity_id = serializers.CharField(read_only=True)
    batch_mode = serializers.BooleanField(write_only=True)
    notify_recipients = serializers.BooleanField(write_only=True)

    def create(self, validated_data):
        badgeclass = validated_data['badgeclass']
        batch_mode = validated_data.pop('batch_mode')
        notify_recipients = validated_data.pop('notify_recipients')
        direct_awards = validated_data.pop('direct_awards')
        user_permissions = badgeclass.get_permissions(validated_data['created_by'])
        if user_permissions['may_award']:
            successfull_direct_awards = []
            try:
                with transaction.atomic():
                    direct_award_bundle = DirectAwardBundle.objects.create(initial_total=direct_awards.__len__(), **validated_data)
                    for direct_award in direct_awards:
                        successfull_direct_awards.append(
                            DirectAward.objects.create(bundle=direct_award_bundle,
                                                       badgeclass=badgeclass,
                                                       **direct_award)
                        )
            except IntegrityError:
                raise BadgrValidationError("A direct award already exists with this eppn for this badgeclass", 999)
            if notify_recipients:
                for da in successfull_direct_awards:
                    da.notify_recipient()
            if batch_mode:
                direct_award_bundle.notify_awarder()
            direct_award_bundle.badgeclass.remove_cached_data(['cached_direct_awards'])
            direct_award_bundle.badgeclass.remove_cached_data(['cached_direct_award_bundles'])

            return direct_award_bundle
        raise BadgrValidationError("You don't have the necessary permissions", 100)
