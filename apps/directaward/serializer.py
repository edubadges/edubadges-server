import threading
import re

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from directaward.models import DirectAward, DirectAwardBundle
from issuer.serializers import BadgeClassSlugRelatedField
from mainsite.exceptions import BadgrValidationError
from directaward.signals import audit_trail_signal


class DirectAwardSerializer(serializers.Serializer):
    class Meta:
        model = DirectAward

    badgeclass = BadgeClassSlugRelatedField(slug_field="entity_id", required=False)
    eppn = serializers.CharField(required=False)
    recipient_email = serializers.EmailField(required=False)
    status = serializers.CharField(required=False)
    evidence_url = serializers.URLField(
        required=False, allow_blank=True, allow_null=True
    )
    narrative = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )
    grade_achieved = serializers.CharField(
        required=False, allow_blank=True, allow_null=True
    )

    def validate_eppn(self, eppn):
        eppn_reg_exp_format = self.context['request'].user.institution.eppn_reg_exp_format
        if eppn_reg_exp_format:
            eppn_re = re.compile(eppn_reg_exp_format, re.IGNORECASE)
            if not bool(eppn_re.match(eppn)):
                raise ValidationError(message="Incorrect eppn format", code="error")
        return eppn

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        audit_trail_signal.send(
            sender=self.__class__,
            user=validated_data["created_by"],
            method="UPDATE",
            summary="Directaward updated",
            request=self.context["request"],
            direct_award_id=validated_data["entity_id"],
        )
        return instance


class DirectAwardBundleSerializer(serializers.Serializer):
    class Meta:
        model = DirectAwardBundle

    badgeclass = BadgeClassSlugRelatedField(slug_field="entity_id", required=False)
    direct_awards = DirectAwardSerializer(many=True, write_only=True)
    entity_id = serializers.CharField(read_only=True)
    sis_user_id = serializers.CharField(
        write_only=True, required=False, allow_null=True, allow_blank=True
    )
    batch_mode = serializers.BooleanField(write_only=True)
    lti_import = serializers.BooleanField(write_only=True)
    status = serializers.CharField(
        write_only=True, default="Active", required=False, allow_null=True
    )
    identifier_type = serializers.CharField(
        write_only=True, default="eppn", allow_null=False
    )
    scheduled_at = serializers.DateTimeField(
        write_only=True, required=False, allow_null=True
    )
    notify_recipients = serializers.BooleanField(write_only=True)

    def create(self, validated_data):
        badgeclass = validated_data["badgeclass"]
        scheduled_at = validated_data.get("scheduled_at")
        if scheduled_at:
            validated_data["status"] = DirectAwardBundle.STATUS_SCHEDULED
        batch_mode = validated_data.pop("batch_mode")
        notify_recipients = validated_data.pop("notify_recipients")
        direct_awards = validated_data.pop("direct_awards")
        user_permissions = badgeclass.get_permissions(validated_data["created_by"])
        if user_permissions["may_award"]:
            successfull_direct_awards = []
            if hasattr(self.context["request"], "sis_api_call") and getattr(
                    self.context["request"], "sis_api_call"
            ):
                validated_data["sis_import"] = True
                validated_data["sis_client_id"] = (
                    badgeclass.issuer.faculty.institution.manage_client_id
                )

            with transaction.atomic():
                direct_award_bundle = DirectAwardBundle.objects.create(
                    initial_total=direct_awards.__len__(), **validated_data
                )
                for direct_award in direct_awards:
                    direct_award["eppn"] = direct_award["eppn"].lower()
                    status = (
                        DirectAward.STATUS_SCHEDULED
                        if scheduled_at
                        else DirectAward.STATUS_UNACCEPTED
                    )
                    direct_award["status"] = status
                    try:
                        da_created = DirectAward.objects.create(
                            bundle=direct_award_bundle,
                            badgeclass=badgeclass,
                            **direct_award,
                        )
                        successfull_direct_awards.append(da_created)
                        audit_trail_signal.send(
                            sender=self.__class__,
                            request=self.context["request"],
                            user=validated_data["created_by"],
                            method="CREATE",
                            summary="Directawards created",
                            direct_award_id=da_created.entity_id,
                        )
                    except IntegrityError:
                        pass
            if notify_recipients and not scheduled_at:

                def send_mail(awards):
                    for da in awards:
                        da.notify_recipient()

                thread = threading.Thread(
                    target=send_mail, args=(successfull_direct_awards,)
                )
                thread.start()
            if batch_mode and not scheduled_at:
                direct_award_bundle.notify_awarder()
            if batch_mode and scheduled_at:
                direct_award_bundle.notify_awarder_for_scheduled()
            direct_award_bundle.badgeclass.remove_cached_data(["cached_direct_awards"])
            direct_award_bundle.badgeclass.remove_cached_data(
                ["cached_direct_award_bundles"]
            )
            return direct_award_bundle
        audit_trail_signal.send(
            sender=self.__class__,
            user=validated_data["created_by"],
            method="CREATE",
            change_summary="No permissions to create directawards",
            request=self.context["request"],
            direct_award_id=0,
        )
        raise BadgrValidationError("You don't have the necessary permissions", 100)
