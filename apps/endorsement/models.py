import cachemodel
from django.db import models

from entity.models import BaseVersionedEntity
from issuer.models import BadgeClass
from mainsite.exceptions import BadgrValidationFieldError, BadgrValidationError
from mainsite.models import BaseAuditedModel


class Endorsement(BaseAuditedModel, BaseVersionedEntity, cachemodel.CacheModel):
    # The source badge class representing the endorser
    endorser = models.ForeignKey(BadgeClass, blank=False, null=False, on_delete=models.CASCADE,
                                 related_name='endorsed')
    # The badge class that is enriched with the actual endorsement
    endorsee = models.ForeignKey(BadgeClass, blank=False, null=False, on_delete=models.CASCADE,
                                 related_name='endorsements')
    claim = models.TextField(blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)

    STATUS_UNACCEPTED = 'Unaccepted'
    STATUS_ACCEPTED = 'Accepted'
    STATUS_REVOKED = 'Revoked'
    STATUS_REJECTED = 'Rejected'
    STATUS_CHOICES = (
        (STATUS_UNACCEPTED, 'Unaccepted'),
        (STATUS_ACCEPTED, 'Unaccepted'),
        (STATUS_REVOKED, 'Revoked'),
        (STATUS_REJECTED, 'Rejected'),
    )

    status = models.CharField(max_length=254, choices=STATUS_CHOICES, default=STATUS_UNACCEPTED)
    rejection_reason = models.CharField(max_length=512, blank=True, null=True, default=None)
    revocation_reason = models.CharField(max_length=512, blank=True, null=True, default=None)

    def validate_unique(self, exclude=None):
        if self.__class__.objects.filter(endorser=self.endorser, endorsee=self.endorsee).exclude(pk=self.pk).exists():
            raise BadgrValidationFieldError('endorser',
                                            "Endorsement with this name already exists for this user.",
                                            936)
        return super(Endorsement, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(Endorsement, self).save(*args, **kwargs)

    def get_permissions(self, user):
        """
        Function that equates permission for this Endorsement to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.endorsee.get_permissions(user)

    def clear_endorsement_cache(self):
        self.endorsee.remove_cached_data(['cached_endorsements'])
        self.endorser.remove_cached_data(['cached_endorsed'])
