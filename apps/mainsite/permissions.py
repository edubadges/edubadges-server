from rest_framework import permissions


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