# encoding: utf-8


from badgeuser.models import BadgeUser
from rest_framework.permissions import BasePermission


class BadgeUserIsAuthenticatedUser(BasePermission):
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, BadgeUser):
            return request.user.pk == obj.pk
        return False
