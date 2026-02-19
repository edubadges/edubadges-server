import urllib.parse
import uuid
import datetime
from django.conf import settings
from django.db import models, IntegrityError
from django.utils.html import strip_tags

from cachemodel.decorators import cached_method
from cachemodel.models import CacheModel
from entity.models import BaseVersionedEntity
from mainsite.exceptions import BadgrValidationError
from mainsite.models import BaseAuditedModel
from mainsite.utils import send_mail, EmailMessageMaker
from mobile_api.push_notifications import send_push_notification


class DirectAward(BaseAuditedModel, BaseVersionedEntity, CacheModel):
    recipient_email = models.EmailField()
    recipient_first_name = models.CharField(max_length=255, blank=True, null=True)
    recipient_surname = models.CharField(max_length=255, blank=True, null=True)
    eppn = models.CharField(max_length=254, blank=True, null=True, default=None)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    bundle = models.ForeignKey('directaward.DirectAwardBundle', null=True, on_delete=models.CASCADE)

    # To create BadgeInstanceEvidence after claim from student
    evidence_url = models.CharField(max_length=2083, blank=True, null=True, default=None)
    narrative = models.TextField(blank=True, null=True, default=None)
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)
    reminders = models.IntegerField(default=0, blank=False, null=False)
    grade_achieved = models.CharField(max_length=254, blank=True, null=True, default=None)

    STATUS_UNACCEPTED = 'Unaccepted'
    STATUS_REVOKED = 'Revoked'
    STATUS_REJECTED = 'Rejected'
    STATUS_SCHEDULED = 'Scheduled'
    STATUS_DELETED = 'Deleted'
    STATUS_CHOICES = (
        (STATUS_UNACCEPTED, 'Unaccepted'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_DELETED, 'Deleted'),
    )
    status = models.CharField(max_length=254, choices=STATUS_CHOICES, default=STATUS_UNACCEPTED)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)
    resend_at = models.DateTimeField(blank=True, null=True, default=None)
    delete_at = models.DateTimeField(blank=True, null=True, default=None)
    expiration_date = models.DateTimeField(blank=True, null=True, default=None)

    def validate_unique(self, exclude=None):
        if ((
                self.__class__.objects.filter(
                    eppn=self.eppn,
                    badgeclass=self.badgeclass,
                    status='Unaccepted',
                    bundle__identifier_type=DirectAwardBundle.IDENTIFIER_EPPN,
                )
                        .exclude(pk=self.pk)
                        .exclude(eppn__isnull=True)
                        .exists()
        ) or self.__class__.objects.filter(
            recipient_email=self.recipient_email,
            badgeclass=self.badgeclass,
            status='Unaccepted',
            bundle__identifier_type=DirectAwardBundle.IDENTIFIER_EMAIL,
        )
                .exclude(pk=self.pk)
                .exclude(recipient_email__isnull=True).exists()):
            raise IntegrityError(
                f"DirectAward with eppn: {self.eppn} / email: {self.recipient_email} and status Unaccepted "
                f"already exists for badgeclass {self.badgeclass.name} ({self.badgeclass.id})."
            )
        return super(DirectAward, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(DirectAward, self).save(*args, **kwargs)

    def revoke(self, revocation_reason):
        if self.status == DirectAward.STATUS_REVOKED:
            raise BadgrValidationError('DirectAward is already revoked', 999)
        if not revocation_reason:
            raise BadgrValidationError('revocation_reason is required', 999)
        self.status = DirectAward.STATUS_REVOKED
        self.revocation_reason = revocation_reason
        self.save()

    def award(self, recipient):
        """Accept the direct award and make an assertion out of it"""
        from issuer.models import BadgeInstance

        if self.bundle.identifier_type == DirectAwardBundle.IDENTIFIER_EPPN:
            if self.eppn not in recipient.eppns:
                raise BadgrValidationError(
                    'Cannot award, eppn does not match',
                    999,
                )

        elif self.bundle.identifier_type == DirectAwardBundle.IDENTIFIER_EMAIL:
            if self.recipient_email != recipient.email:
                raise BadgrValidationError(
                    'Cannot award, email does not match',
                    999,
                )

        evidence = None
        if self.evidence_url or self.narrative:
            evidence = [
                {
                    'evidence_url': self.evidence_url,
                    'narrative': self.narrative,
                    'description': self.description,
                    'name': self.name,
                }
            ]
        expires_at = None
        if self.badgeclass.expiration_period:
            expires_at = (
                    datetime.datetime.now().replace(microsecond=0, second=0, minute=0, hour=0)
                    + self.badgeclass.expiration_period
            )

        # The validated name should take precedence over the user filled in recipient name
        recipient_name = None
        if recipient.validated_name:
            recipient_name = recipient.validated_name
        elif self.recipient_first_name and self.recipient_surname:
            recipient_name = f'{self.recipient_first_name} {self.recipient_surname}'

        assertion = self.badgeclass.issue(
            recipient=recipient,
            created_by=self.created_by,
            acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED,
            recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
            expires_at=expires_at,
            send_email=False,
            issued_on=self.created_at,
            award_type=BadgeInstance.AWARD_TYPE_DIRECT_AWARD,
            direct_award_bundle=self.bundle,
            evidence=evidence,
            include_evidence=evidence is not None,
            grade_achieved=self.grade_achieved,
            recipient_name=recipient_name,
            enforce_validated_name=False,
        )
        # delete any pending enrollments for this badgeclass and user
        recipient.cached_pending_enrollments().filter(badge_class=self.badgeclass).delete()
        recipient.remove_cached_data(['cached_pending_enrollments'])
        return assertion

    def get_permissions(self, user):
        """
        Function that equates permission for this DirectAward to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badgeclass.get_permissions(user)

    def notify_recipient(self):
        from badgeuser.models import BadgeUser
        html_message = EmailMessageMaker.create_direct_award_student_mail(self)
        plain_text = strip_tags(html_message)
        send_mail(
            subject='Je hebt een edubadge ontvangen. You received an edubadge. Claim it now!',
            message=plain_text,
            html_message=html_message,
            recipient_list=[self.recipient_email],
        )

        user = BadgeUser.objects.filter(email=self.recipient_email).first()
        send_push_notification(
            user=user,
            title="Edubadge received",
            body="You earned an edubadge, claim it now!",
            data={
                "title_key": "push.badge_received_title",
                "body_key": "push.badge_received_body",
                "badge": self.name,
            }
        )



class DirectAwardBundle(BaseAuditedModel, BaseVersionedEntity, CacheModel):
    initial_total = models.IntegerField()
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    lti_import = models.BooleanField(default=False)
    sis_import = models.BooleanField(default=False)
    sis_user_id = models.CharField(max_length=254, blank=True, null=True)
    sis_client_id = models.CharField(max_length=254, blank=True, null=True)
    # This is the number of DA's that are removed, because they were not claimed on time
    direct_award_expired_count = models.IntegerField(default=0)
    # This is the number of DA's that are removed directly by the institution staff
    direct_award_removed_count = models.IntegerField(default=0)

    STATUS_SCHEDULED = 'Scheduled'
    STATUS_ACTIVE = 'Active'
    STATUS_CHOICES = (
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_ACTIVE, 'Active'),
    )
    status = models.CharField(max_length=254, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    IDENTIFIER_EPPN = 'eppn'
    IDENTIFIER_EMAIL = 'email'
    IDENTIFIER_TYPES = (
        (IDENTIFIER_EPPN, 'eppn'),
        (IDENTIFIER_EMAIL, 'email'),
    )
    identifier_type = models.CharField(max_length=254, choices=IDENTIFIER_TYPES, default=IDENTIFIER_EPPN)
    scheduled_at = models.DateTimeField(blank=True, null=True, default=None)

    @property
    def assertion_count(self):
        from issuer.models import BadgeInstance

        return BadgeInstance.objects.filter(direct_award_bundle=self, revoked=False).count()

    @property
    def direct_award_count(self):
        return DirectAward.objects.filter(bundle=self, status='Unaccepted').count()

    @property
    def direct_award_rejected_count(self):
        return DirectAward.objects.filter(bundle=self, status='Rejected').count()

    @property
    def direct_award_scheduled_count(self):
        return DirectAward.objects.filter(bundle=self, status='Scheduled').count()

    @property
    def direct_award_deleted_count(self):
        return DirectAward.objects.filter(bundle=self, status='Deleted').count()

    @property
    def direct_award_revoked_count(self):
        from issuer.models import BadgeInstance

        revoked_count = BadgeInstance.objects.filter(direct_award_bundle=self, revoked=True).count()
        return revoked_count + DirectAward.objects.filter(bundle=self, status='Revoked').count()

    @property
    def url(self):
        return urllib.parse.urljoin(
            settings.UI_URL,
            'badgeclass/{}/direct-awards-bundles'.format(self.badgeclass.entity_id),
        )

    @cached_method()
    def cached_direct_awards(self):
        return list(DirectAward.objects.filter(bundle=self))

    @property
    def recipient_emails(self):
        return [da.recipient_email for da in self.cached_direct_awards()]

    def notify_recipients(self):
        from badgeuser.models import BadgeUser
        html_message = EmailMessageMaker.create_direct_award_student_mail(self)
        plain_text = strip_tags(html_message)
        send_mail(
            subject='Je hebt een edubadge ontvangen. You received an edubadge. Claim it now!',
            message=plain_text,
            html_message=html_message,
            bcc=self.recipient_emails,
        )

        for user in BadgeUser.objects.filter(email__in=self.recipient_emails):
            send_push_notification(
                user=user,
                title="Edubadge received",
                body="You earned an edubadge, claim it now!",
                data={
                    "title_key": "push.badge_received_title",
                    "body_key": "push.badge_received_body",
                    "badge": self.badgeclass.name,
                }
            )

    def notify_awarder(self):
        html_message = EmailMessageMaker.create_direct_award_bundle_mail(self)
        plain_text = strip_tags(html_message)
        send_mail(
            subject='You have awarded Edubadges!',
            message=plain_text,
            html_message=html_message,
            recipient_list=[self.created_by.email],
        )

    def notify_awarder_for_scheduled(self):
        html_message = EmailMessageMaker.create_scheduled_direct_award_bundle_mail(self)
        send_mail(
            subject='You have scheduled to award Edubadges!',
            message=None,
            html_message=html_message,
            recipient_list=[self.created_by.email],
        )


class DirectAwardAuditTrail(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    login_IP = models.GenericIPAddressField(null=True, blank=True)
    action_datetime = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=254, blank=True)
    user_agent_info = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=40)
    change_summary = models.CharField(max_length=199, blank=True)
    direct_award = models.ForeignKey('directaward.DirectAward', on_delete=models.SET_NULL, null=True, blank=True)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.SET_NULL, null=True, blank=True)
