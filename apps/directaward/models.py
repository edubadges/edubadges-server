import cachemodel

from django.db import models, IntegrityError

from entity.models import BaseVersionedEntity
from issuer.models import BadgeInstance
from mainsite.models import BaseAuditedModel


class DirectAward(BaseAuditedModel, BaseVersionedEntity,  cachemodel.CacheModel):

    recipient_email = models.EmailField()
    recipient = models.ForeignKey('badgeuser.BadgeUser', blank=True, null=True, on_delete=models.CASCADE)
    eppn = models.CharField(max_length=254)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    ACCEPTANCE_UNACCEPTED = 'Unaccepted'
    ACCEPTANCE_ACCEPTED = 'Accepted'
    ACCEPTANCE_REJECTED = 'Rejected'
    ACCEPTANCE_CHOICES = (
        (ACCEPTANCE_UNACCEPTED, 'Unaccepted'),
        (ACCEPTANCE_ACCEPTED, 'Accepted'),
        (ACCEPTANCE_REJECTED, 'Rejected'),
    )
    acceptance = models.CharField(max_length=254, choices=ACCEPTANCE_CHOICES, default=ACCEPTANCE_UNACCEPTED)

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

    def award(self):
        """Accept the direct award and make an assertion out of it"""
        return self.badgeclass.issue(recipient=self.recipient,
                                     created_by=self.created_by,
                                     acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED,
                                     recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                                     notify_recipient=False)

    def reject(self):
        self.acceptance = self.ACCEPTANCE_REJECTED
        self.save()

    def get_permissions(self, user):
        """
        Function that equates permission for this DirectAward to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badgeclass.get_permissions(user)
