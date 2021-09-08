import urllib

import cachemodel
from django.conf import settings
from django.db import models, IntegrityError
from django.utils.html import strip_tags

from entity.models import BaseVersionedEntity
from mainsite.exceptions import BadgrValidationError
from mainsite.models import BaseAuditedModel, EmailBlacklist
from mainsite.utils import send_mail, EmailMessageMaker


class DirectAward(BaseAuditedModel, BaseVersionedEntity, cachemodel.CacheModel):
    recipient_email = models.EmailField()
    eppn = models.CharField(max_length=254)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    bundle = models.ForeignKey('directaward.DirectAwardBundle', null=True, on_delete=models.CASCADE)

    # To create BadgeInstanceEvidence after claim from student
    evidence_url = models.CharField(max_length=2083, blank=True, null=True, default=None)
    narrative = models.TextField(blank=True, null=True, default=None)
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)

    STATUS_UNACCEPTED = 'Unaccepted'
    STATUS_REVOKED = 'Revoked'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = (
        (STATUS_UNACCEPTED, 'Unaccepted'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_REJECTED, 'Rejected'),
    )
    status = models.CharField(max_length=254, choices=STATUS_CHOICES, default=STATUS_UNACCEPTED)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)

    def validate_unique(self, exclude=None):
        if self.__class__.objects \
                .filter(eppn=self.eppn, badgeclass=self.badgeclass, status='Unaccepted') \
                .exclude(pk=self.pk) \
                .exists():
            raise IntegrityError(
                "DirectAward with this eppn and status Unaccepted already exists in the same badgeclass.")
        return super(DirectAward, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(DirectAward, self).save(*args, **kwargs)

    def revoke(self, revocation_reason):
        if self.status == DirectAward.STATUS_REVOKED:
            raise BadgrValidationError("DirectAward is already revoked", 999)
        if not revocation_reason:
            raise BadgrValidationError("revocation_reason is required", 999)
        self.status = DirectAward.STATUS_REVOKED
        self.revocation_reason = revocation_reason
        self.save()

    def award(self, recipient):
        """Accept the direct award and make an assertion out of it"""
        from issuer.models import BadgeInstance
        if self.eppn not in recipient.eppns:
            raise BadgrValidationError('Cannot award, eppn does not match', 999)

        institution = self.badgeclass.institution
        identifiers = [inst.identifier for inst in self.badgeclass.award_allowed_institutions.all()] + [
            institution.identifier]
        schac_homes = recipient.schac_homes
        if self.badgeclass.formal:
            allowed = institution.identifier in schac_homes
        else:
            allowed = any(identifier in schac_homes for identifier in identifiers) or recipient.validated_name
        if not allowed:
            raise BadgrValidationError('Cannot award, you are not a member of the institution of the badgeclass', 999)
        evidence = None
        if self.evidence_url or self.narrative:
            evidence = [{
                'evidence_url': self.evidence_url,
                'narrative': self.narrative,
                'description': self.description,
                'name': self.name
            }]
        assertion = self.badgeclass.issue(recipient=recipient,
                                          created_by=self.created_by,
                                          acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED,
                                          recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                                          send_email=False,
                                          award_type=BadgeInstance.AWARD_TYPE_DIRECT_AWARD,
                                          direct_award_bundle=self.bundle,
                                          evidence=evidence,
                                          include_evidence=evidence is not None)
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
        html_message = EmailMessageMaker.create_direct_award_student_mail(self)
        try:
            EmailBlacklist.objects.get(email=self.recipient_email)
        except EmailBlacklist.DoesNotExist:
            # Allow sending, as this email is not blacklisted.
            plain_text = strip_tags(html_message)
            send_mail(subject='Congratulations, you earned an edubadge!',
                      message=plain_text, html_message=html_message, recipient_list=[self.recipient_email])


class DirectAwardBundle(BaseAuditedModel, BaseVersionedEntity, cachemodel.CacheModel):
    initial_total = models.IntegerField()
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)

    @property
    def assertion_count(self):
        from issuer.models import BadgeInstance
        return BadgeInstance.objects.filter(direct_award_bundle=self).count()

    @property
    def direct_award_count(self):
        return DirectAward.objects.filter(bundle=self, status='Unaccepted').count()

    @property
    def direct_award_rejected_count(self):
        return DirectAward.objects.filter(bundle=self, status='Rejected').count()

    @property
    def direct_award_revoked_count(self):
        return DirectAward.objects.filter(bundle=self, status='Revoked').count()

    @property
    def url(self):
        return urllib.parse.urljoin(settings.UI_URL,
                                    'badgeclass/{}/direct-awards-bundles'.format(self.badgeclass.entity_id))

    @cachemodel.cached_method()
    def cached_direct_awards(self):
        return list(DirectAward.objects.filter(bundle=self))

    @property
    def recipient_emails(self):
        return [da.recipient_email for da in self.cached_direct_awards()]

    def notify_recipients(self):
        html_message = EmailMessageMaker.create_direct_award_student_mail(self)
        plain_text = strip_tags(html_message)
        send_mail(subject='Congratulations, you earned an edubadge!',
                  message=plain_text, html_message=html_message, bcc=self.recipient_emails)

    def notify_awarder(self):
        html_message = EmailMessageMaker.create_direct_award_bundle_mail(self)
        plain_text = strip_tags(html_message)
        send_mail(subject='You have awarded Edubadges!',
                  message=plain_text, html_message=html_message, recipient_list=[self.created_by.email])
