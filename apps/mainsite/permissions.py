import logging

from django.conf import settings
from rest_framework import permissions
from django.contrib.auth.mixins import PermissionRequiredMixin

logger = logging.getLogger('Badgr.Debug')


class AuthenticatedWithVerifiedEmail(permissions.BasePermission):
    """
    Allows access only to authenticated users who have verified email addresses.
    """
    message = "This function only available to authenticated users with confirmed email addresses."

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.verified


class LocalDevelopModePermissionMixin(PermissionRequiredMixin):
    """
    Checks to see if LOCAL_DEVELOPMENT_MODE is set to true
    """

    def has_permission(self):
        try:
            return settings.LOCAL_DEVELOPMENT_MODE is True
        except AttributeError:
            return False