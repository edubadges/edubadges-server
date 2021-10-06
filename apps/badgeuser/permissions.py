# encoding: utf-8


from rest_framework.permissions import BasePermission

from badgeuser.models import BadgeUser


class BadgeUserIsAuthenticatedUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, BadgeUser):
            return request.user.pk == obj.pk
        return False


class InstitutionAdmin(BasePermission):
    """
    Allows access only to institution admin
    """

    def has_permission(self, request, view):
        user = request.user
        return user and user.institutionstaff_set.exists() and user.institutionstaff_set.first().may_administrate_users
