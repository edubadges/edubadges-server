import cachemodel

from django.conf import settings
from django.db import models, IntegrityError
from django.utils.html import strip_tags

from entity.models import BaseVersionedEntity
from mainsite.exceptions import BadgrValidationError
from mainsite.models import BaseAuditedModel, EmailBlacklist
from mainsite.utils import open_mail_in_browser, send_mail, EmailMessageMaker


class DirectAward(BaseAuditedModel, BaseVersionedEntity,  cachemodel.CacheModel):

    recipient_email = models.EmailField()
    eppn = models.CharField(max_length=254)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    bundle = models.ForeignKey('directaward.DirectAwardBundle', null=True, on_delete=models.CASCADE)

    def validate_unique(self, exclude=None):
        if self.__class__.objects \
                .filter(eppn=self.eppn, badgeclass=self.badgeclass) \
                .exclude(pk=self.pk) \
                .exists():
            raise IntegrityError("DirectAward with this eppn already exists in the same badgeclass.")
        return super(DirectAward, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(DirectAward, self).save(*args, **kwargs)

    def award(self, recipient):
        """Accept the direct award and make an assertion out of it"""
        from issuer.models import BadgeInstance
        if self.eppn not in recipient.eppns:
            raise BadgrValidationError('Cannot award, eppn does not match', 999)
        if self.badgeclass.institution.identifier not in recipient.schac_homes:
            raise BadgrValidationError('Cannot award, you are not a member of the institution of the badgeclass', 999)
        return self.badgeclass.issue(recipient=recipient,
                                     created_by=self.created_by,
                                     acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED,
                                     recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                                     send_email=False,
                                     award_type=BadgeInstance.AWARD_TYPE_DIRECT_AWARD)

    def get_permissions(self, user):
        """
        Function that equates permission for this DirectAward to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badgeclass.get_permissions(user)

    def notify_recipient(self):
        html_message = EmailMessageMaker.create_direct_award_student_mail(self)
        if settings.LOCAL_DEVELOPMENT_MODE:
            open_mail_in_browser(html_message)
        try:
            EmailBlacklist.objects.get(email=self.recipient_email)
        except EmailBlacklist.DoesNotExist:
            # Allow sending, as this email is not blacklisted.
            plain_text = strip_tags(html_message)
            send_mail(subject='Congratulations, you earned an edubadge!',
                      message=plain_text, html_message=html_message, recipient_list=[self.recipient_email])


class DirectAwardBundle(BaseAuditedModel, BaseVersionedEntity,  cachemodel.CacheModel):

    initial_total = models.IntegerField()
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)


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

