import cachemodel

from django.db import models

from entity.models import BaseVersionedEntity
from issuer.models import BadgeInstance
from mainsite.models import BaseAuditedModel


class DirectAward(BaseAuditedModel, BaseVersionedEntity,  cachemodel.CacheModel):

    recipient_email = models.EmailField()
    recipient = models.ForeignKey('badgeuser.BadgeUser', blank=True, null=True, on_delete=models.CASCADE)
    eppn = models.CharField(max_length=254)
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)


    def award(self):
        """Accept the direct award and make an assertion out of it"""
        return self.badgeclass.issue(recipient=self.recipient,
                                     created_by=self.created_by,
                                     acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED,
                                     recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                                     notify_recipient=False)

    def get_permissions(self, user):
        """
        Function that equates permission for this DirectAward to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badgeclass.get_permissions(user)
