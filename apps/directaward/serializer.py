import datetime
import re
import threading

from django.core.exceptions import ValidationError, BadRequest
from django.db import transaction
from rest_framework import serializers

from directaward.models import DirectAward, DirectAwardBundle, DirectAwardAuditTrail, DirectAwardMonitoring
from directaward.signals import audit_trail_signal
from issuer.models import BadgeClass
from issuer.serializers import BadgeClassSlugRelatedField
from mainsite import settings
from mainsite.exceptions import BadgrValidationError


class DirectAwardSerializer(serializers.Serializer):
    class Meta:
        model = DirectAward

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    eppn = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    recipient_email = serializers.EmailField(required=False)
    status = serializers.CharField(required=False)
    evidence_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    narrative = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    grade_achieved = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate_eppn(self, eppn):
        eppn_reg_exp_format = self.context['request'].user.institution.eppn_reg_exp_format
        # For email identifier_type we don't validate eppn
        eppn_required = self.root.initial_data.get('identifier_type', 'eppn') == 'eppn'
        if eppn_reg_exp_format and eppn_required:
            eppn_re = re.compile(eppn_reg_exp_format, re.IGNORECASE)
            if not bool(eppn_re.match(eppn)):
                raise ValidationError(message='Incorrect eppn format', code='error')
        return eppn

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        audit_trail_signal.send(
            sender=self.__class__,
            user=validated_data['created_by'],
            method='UPDATE',
            summary='Directaward updated',
            request=self.context['request'],
            direct_award_id=validated_data['entity_id'],
        )
        return instance


class DirectAwardBundleSerializer(serializers.Serializer):
    class Meta:
        model = DirectAwardBundle

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    direct_awards = DirectAwardSerializer(many=True, write_only=True)
    entity_id = serializers.CharField(read_only=True)
    sis_user_id = serializers.CharField(write_only=True, required=False, allow_null=True, allow_blank=True)
    batch_mode = serializers.BooleanField(write_only=True, default=False, required=False, allow_null=True)
    lti_import = serializers.BooleanField(write_only=True, default=False, required=False, allow_null=True)
    status = serializers.CharField(write_only=True, default='Active', required=False, allow_null=True)
    identifier_type = serializers.CharField(write_only=True, default='eppn', allow_null=False)
    scheduled_at = serializers.DateTimeField(write_only=True, required=False, allow_null=True)

    notify_recipients = serializers.BooleanField(write_only=True)

    def create(self, validated_data):
        badgeclass = validated_data['badgeclass']
        if badgeclass.direct_awarding_disabled:
            raise BadRequest(f'Direct awarding disabled for {badgeclass.name}')
        if badgeclass.is_private:
            raise BadRequest(f' Badgeclass {badgeclass.name} is not published. Direct awarding not allowed')

        scheduled_at = validated_data.get('scheduled_at')
        if scheduled_at:
            validated_data['status'] = DirectAwardBundle.STATUS_SCHEDULED
        batch_mode = validated_data.pop('batch_mode')
        notify_recipients = validated_data.pop('notify_recipients')
        direct_awards = validated_data.pop('direct_awards')
        requires_approval = validated_data.pop('requires_approval', False)
        user_permissions = badgeclass.get_permissions(validated_data['created_by'])
        if user_permissions['may_award']:
            successful_direct_awards = []
            un_successful_direct_awards = []
            if hasattr(self.context['request'], 'sis_api_call') and getattr(self.context['request'], 'sis_api_call'):
                validated_data['sis_import'] = True
                validated_data['sis_client_id'] = badgeclass.issuer.faculty.institution.manage_client_id

            with transaction.atomic():
                direct_award_bundle = DirectAwardBundle.objects.create(
                    initial_total=direct_awards.__len__(), **validated_data
                )
                direct_award_bundle.badgeclass.remove_cached_data(['cached_direct_awards'])
                direct_award_bundle.badgeclass.remove_cached_data(['cached_direct_award_bundles'])

                eppn_required = validated_data.get('identifier_type', 'eppn') == 'eppn'
                now = datetime.datetime.now(datetime.timezone.utc)
                expiration_date = now + datetime.timedelta(days=settings.EXPIRY_DIRECT_AWARDS_DELETION_THRESHOLD_DAYS)
                for direct_award in direct_awards:
                    # Not required and already validated
                    direct_award['recipient_email'] = direct_award['recipient_email'].lower()
                    direct_award['eppn'] = direct_award['eppn'].lower() if eppn_required else None

                    # All awards start as pending approval by default now
                    direct_award['status'] = DirectAward.STATUS_PENDING_APPROVAL
                    direct_award['created_by'] = validated_data['created_by']
                    direct_award['expiration_date'] = expiration_date
                    try:
                        da_created = DirectAward.objects.create(
                            bundle=direct_award_bundle,
                            badgeclass=badgeclass,
                            **direct_award,
                        )

                        # Check thresholds and create monitoring record
                        threshold_passed = da_created.check_thresholds()

                        if threshold_passed:
                            # Auto-approved, create monitoring record
                            DirectAwardMonitoring.objects.create(
                                direct_award=da_created, monitoring_status='Auto Approved', auto_approved=True
                            )
                        else:
                            # Blocked by thresholds, create monitoring record
                            DirectAwardMonitoring.objects.create(
                                direct_award=da_created,
                                monitoring_status='Blocked',
                                auto_approved=False,
                                block_reason='Threshold violation detected',
                            )

                        successful_direct_awards.append(da_created)
                        audit_trail_signal.send(
                            sender=self.__class__,
                            request=self.context['request'],
                            user=validated_data['created_by'],
                            method='CREATE',
                            summary='Directawards created',
                            direct_award_id=da_created.entity_id,
                            badgeclass_id=da_created.badgeclass_id,
                        )
                    except Exception as e:
                        un_successful_direct_awards.append(
                            {'error': str(e), 'eppn': direct_award['eppn'], 'email': direct_award['recipient_email']}
                        )
                if not successful_direct_awards:
                    raise BadRequest(
                        f'No valid DirectAwards are created. All of them were rejected: '
                        f'{str(un_successful_direct_awards)}'
                    )

            if notify_recipients and not scheduled_at:

                def send_mail(awards):
                    for da in awards:
                        da.notify_recipient()

                thread = threading.Thread(target=send_mail, args=(successful_direct_awards,))
                thread.start()
            if batch_mode and not scheduled_at:
                direct_award_bundle.notify_awarder()
            if batch_mode and scheduled_at:
                direct_award_bundle.notify_awarder_for_scheduled()
            if un_successful_direct_awards:
                direct_award_bundle.un_successful_direct_award = un_successful_direct_awards
            return direct_award_bundle

        audit_trail_signal.send(
            sender=self.__class__,
            user=validated_data['created_by'],
            method='CREATE',
            change_summary='No permissions to create directawards',
            request=self.context['request'],
            direct_award_id=0,
            badgeclass_id=0,
        )
        raise BadgrValidationError("You don't have the necessary permissions", 100)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'un_successful_direct_award'):
            data['un_successful_direct_award'] = instance.un_successful_direct_award
        return data


class DirectAwardMonitoringSerializer(serializers.ModelSerializer):
    class Meta:
        model = DirectAwardMonitoring
        fields = [
            'monitoring_status',
            'reviewed_by',
            'review_date',
            'admin_comments',
            'block_reason',
            'threshold_violations',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['monitoring_status', 'reviewed_by', 'review_date', 'created_at', 'updated_at']


class DirectAwardAuditTrailSerializer(serializers.ModelSerializer):
    badgeclass_name = serializers.CharField(
        source='badgeclass.name',
        read_only=True,
    )
    institution_name = serializers.CharField(
        source='badgeclass.issuer.faculty.institution.name',
        read_only=True,
    )
    recipient_email = serializers.EmailField(source='direct_award.recipient_email', read_only=True)
    recipient_eppn = serializers.CharField(source='direct_award.eppn', read_only=True)

    class Meta:
        model = DirectAwardAuditTrail
        fields = [
            'action_datetime',
            'user',
            'badgeclass_name',
            'institution_name',
            'recipient_email',
            'recipient_eppn',
        ]
