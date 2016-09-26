from rest_framework import permissions

from badgeuser.models import CachedEmailAddress


class IsOwner(permissions.BasePermission):
    """
    Allows only owners of an object to read or write it via the API
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsRequestUser(permissions.BasePermission):
    """
    Allows users to be able to act on their own profile, but not on others.
    """
    def has_object_permission(self, request, view, obj):
        return obj == request.user


class AuthenticatedWithVerifiedEmail(permissions.BasePermission):
    """
    Allows access only to authenticated users who have verified email addresses.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated() and \
               [e for e in request.user.cached_emails() if e.verified and e.primary]
