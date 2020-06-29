from django.db import models
from django.forms.models import model_to_dict
from rest_framework import serializers

from entity.models import BaseVersionedEntity
from mainsite.exceptions import BadgrValidationError
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

    @classmethod
    def empty_permissions(cls):
        """convenience class method to represent NO permissions"""
        return {'may_create': False,
                'may_read': False,
                'may_update': False,
                'may_delete': False,
                'may_award': False,
                'may_sign': False,
                'may_administrate_users': False}

    @classmethod
    def full_permissions(cls):
        """convenience class method to represent FULL permissions"""
        return {'may_create': True,
                'may_read': True,
                'may_update': True,
                'may_delete': True,
                'may_award': True,
                'may_sign': True,
                'may_administrate_users': True}

    @property
    def permissions(self):
        return model_to_dict(self, fields = ['may_create',
                                             'may_read',
                                             'may_update',
                                             'may_delete',
                                             'may_award',
                                             'may_sign',
                                             'may_administrate_users'])
    @property
    def has_a_permission(self):
        """check to see if at least one permission set to True"""
        return self.may_create or self.may_read or self.may_update or self.may_delete \
               or self.may_award or self.may_sign or self.may_administrate_users

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

    def _empty_user_cached_staff(self):
        object_class_name = self.object.__class__.__name__.lower()
        if object_class_name == 'institution':
            self.user.remove_cached_data(['cached_institution_staff'])
        else:
            self.user.remove_cached_data(['cached_{}_staffs'.format(object_class_name)])

    def _user_has_other_membership_in_branch(self, user):
        """check to see if given user already has another staff membership in the current branch"""
        user_staff_memberships_in_branch = self.object.get_all_staff_memberships_in_current_branch(user)
        return bool([staff for staff in user_staff_memberships_in_branch if staff.user == user and staff != self])

    def save(self, *args, **kwargs):
        if self._user_has_other_membership_in_branch(self.user):
            raise serializers.ValidationError('Cannot save staff membership, there is a conflicting staff membership.')
        super(PermissionedRelationshipBase, self).save()
        self.object.remove_cached_data(['cached_staff'])
        self._empty_user_cached_staff()

    def delete(self, *args, **kwargs):
        publish_object = kwargs.pop('publish_object', True)
        super(PermissionedRelationshipBase, self).delete()
        if publish_object:
            self.object.remove_cached_data(['cached_staff'])  # update permissions instantly
        self._empty_user_cached_staff()

    @property
    def cached_user(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(pk=self.user_id)


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

    def _is_last_staff_membership(self):
        there_are_other_staffs = bool(InstitutionStaff.objects.filter(institution=self.institution,
                                                                      may_administrate_users=True).exclude(pk=self.pk))
        return not there_are_other_staffs

    def delete(self, *args, **kwargs):
        if self._is_last_staff_membership():
            raise BadgrValidationError('Cannot remove the last staff membership of this institution.', 500)
        return super(InstitutionStaff, self).delete(*args, **kwargs)


class FacultyStaff(PermissionedRelationshipBase):
    """
    Many2Many realtionship between Faculty and users, with permissions added to the relationship
    """
    faculty = models.ForeignKey('institution.Faculty', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('faculty', 'user')

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

    @property
    def may_become_signer(self):
        # return self.user.may_sign_assertions and SymmetricKey.objects.filter(user=self.user, current=True).exists()
        return SymmetricKey.objects.filter(user=self.user, current=True).exists()

    @property
    def is_signer(self):
        return self.may_sign


class BadgeClassStaff(PermissionedRelationshipBase):

    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('badgeclass', 'user')

    @property
    def object(self):
        return self.badgeclass
