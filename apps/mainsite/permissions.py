import logging

from rest_framework import permissions

logger = logging.getLogger('Badgr.Debug')


class AuthenticatedWithVerifiedEmail(permissions.BasePermission):
    """
    Allows access only to authenticated users who have verified email addresses.
    """
    message = "This function only available to authenticated users with confirmed email addresses."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.verified


class CannotDeleteWithChildren(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            if obj.children:
                return False
        return True


class TeachPermission(permissions.BasePermission):
    """
    Allows access only to teachers
    """

    def has_permission(self, request, view):
        return request.user and hasattr(request.user, 'is_teacher') and request.user.is_teacher


class MobileAPIPermission(permissions.BasePermission):
    """
    Allows access only to student
    """

    def has_permission(self, request, view):
        return hasattr(request, 'mobile_api_call') and request.mobile_api_call
