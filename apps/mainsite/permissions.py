from rest_framework import permissions

from badgeuser.models import CachedEmailAddress

import logging
logger=logging.getLogger('Badgr.Debug')            

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
    message = "This function only available to authenticated users with confirmed email addresses."

    def has_permission(self, request, view):
        result = request.user and request.user.is_authenticated() and request.user.verified
        if not result:
            log = {'message':self.message, 
                   'request.user': request.user, 
                   'is_authenticated': request.user.is_authenticated(),
                   'verified': request.user.verified} 
            logger.error(log)
        return result
