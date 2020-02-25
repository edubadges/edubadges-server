import cachemodel
from django.db import models
from django.forms.models import model_to_dict
from signing.models import SymmetricKey


class PermissionedRelationshipMixin(models.Model):
    """
    Abstract base class used for inheritance in all the Staff Many2Many relationship models
    """
    user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.CASCADE)
    create = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    update = models.BooleanField(default=False)
    destroy = models.BooleanField(default=False)
    award = models.BooleanField(default=False)
    sign = models.BooleanField(default=False)
    administrate_users = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def permissions(self):
        return model_to_dict(self, fields = ['create', 'read', 'update',
                                            'destroy', 'award', 'administrate_users'])

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


class InstitutionStaff(PermissionedRelationshipMixin, cachemodel.CacheModel):
    """
    Many2Many realtionship between Institution and users, with permissions added to the relationship
    """
    institution = models.ForeignKey('institution.Institution', on_delete=models.CASCADE)

    class Meta:
        # For now only one institution per user
        constraints = [
            models.UniqueConstraint(fields=['user', 'institution'], name='unique_institution_staff_membership')
        ]

    @property
    def object(self):
        return self.institution

    @property
    def serializer_class(self):
        from staff.serializers import InstitutionStaffSerializer
        return InstitutionStaffSerializer


class FacultyStaff(PermissionedRelationshipMixin, cachemodel.CacheModel):
    """
    Many2Many realtionship between Faculty and users, with permissions added to the relationship
    """
    faculty = models.ForeignKey('institution.Faculty', on_delete=models.CASCADE)

    @property
    def object(self):
        return self.faculty

    @property
    def serializer_class(self):
        from staff.serializers import FacultyStaffSerializer
        return FacultyStaffSerializer


class IssuerStaff(PermissionedRelationshipMixin, cachemodel.CacheModel):
    """
    Many2Many realtionship between Issuer and users, with permissions added to the relationship
    """
    issuer = models.ForeignKey('issuer.Issuer', on_delete=models.CASCADE)
    # role = models.CharField(max_length=254, choices=ROLE_CHOICES, default=ROLE_STAFF)

    class Meta:
        unique_together = ('issuer', 'user')

    @property
    def object(self):
        return self.issuer

    @property
    def serializer_class(self):
        from staff.serializers import IssuerStaffSerializer
        return IssuerStaffSerializer

    def publish(self):
        super(IssuerStaff, self).publish()
        self.issuer.publish()
        self.user.publish()

    def delete(self, *args, **kwargs):
        publish_issuer = kwargs.pop('publish_issuer', True)
        super(IssuerStaff, self).delete()
        if publish_issuer:
            self.issuer.publish()
        self.user.publish()

    @property
    def may_become_signer(self):
        return self.user.may_sign_assertions and SymmetricKey.objects.filter(user=self.user, current=True).exists()

    @property
    def is_signer(self):
        return self.sign

    @property
    def cached_user(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(pk=self.user_id)

    @property
    def cached_issuer(self):
        from issuer.models import Issuer
        return Issuer.cached.get(pk=self.issuer_id)


class BadgeClassStaff(PermissionedRelationshipMixin, cachemodel.CacheModel):

    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)

    @property
    def object(self):
        return self.badgeclass

    @property
    def serializer_class(self):
        from staff.serializers import BadgeClassStaffSerializer
        return BadgeClassStaffSerializer
