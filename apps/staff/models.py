from django.db import models
from django.forms.models import model_to_dict
from entity.models import BaseVersionedEntity
from signing.models import SymmetricKey


class PermissionedRelationshipBase(BaseVersionedEntity):
    """
    Abstract base class used for inheritance in all the Staff Many2Many relationship models
    """
    user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    may_create = models.BooleanField(default=False)
    may_read = models.BooleanField(default=False)
    may_update = models.BooleanField(default=False)
    may_delete = models.BooleanField(default=False)
    may_award = models.BooleanField(default=False)
    may_sign = models.BooleanField(default=False)
    may_administrate_users = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def permissions(self):
        return model_to_dict(self, fields = ['may_create',
                                             'may_read',
                                             'may_update',
                                             'may_delete',
                                             'may_award',
                                             'may_sign',
                                             'may_administrate_users'])

    def has_permissions(self, permissions):
        """
        checks to see if all permissions are there
        :param permissions: list of permissions
        :return: Bool
        """
        has_perm_count = 0
        own_perms = self.permissions
        for perm in permissions:
            if own_perms[perm]:
                has_perm_count += 1
        return len(permissions) == has_perm_count

    def publish(self):
        super(PermissionedRelationshipBase, self).publish()
        self.object.publish()
        self.user.publish()


class InstitutionStaff(PermissionedRelationshipBase):
    """
    Many2Many realtionship between Institution and users, with permissions added to the relationship
    """
    institution = models.ForeignKey('institution.Institution', on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'institution'], name='unique_institution_staff_membership')
        ]

    @property
    def object(self):
        return self.institution


class FacultyStaff(PermissionedRelationshipBase):
    """
    Many2Many realtionship between Faculty and users, with permissions added to the relationship
    """
    faculty = models.ForeignKey('institution.Faculty', on_delete=models.CASCADE)

    @property
    def object(self):
        return self.faculty


class IssuerStaff(PermissionedRelationshipBase):
    """
    Many2Many realtionship between Issuer and users, with permissions added to the relationship
    """
    issuer = models.ForeignKey('issuer.Issuer', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('issuer', 'user')

    @property
    def object(self):
        return self.issuer

    def delete(self, *args, **kwargs):
        publish_issuer = kwargs.pop('publish_issuer', True)
        super(IssuerStaff, self).delete()
        if publish_issuer:
            self.issuer.publish()
        self.user.publish()

    @property
    def may_become_signer(self):
        # return self.user.may_sign_assertions and SymmetricKey.objects.filter(user=self.user, current=True).exists()
        return SymmetricKey.objects.filter(user=self.user, current=True).exists()

    @property
    def is_signer(self):
        return self.may_sign


class BadgeClassStaff(PermissionedRelationshipBase):

    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)

    @property
    def object(self):
        return self.badgeclass
