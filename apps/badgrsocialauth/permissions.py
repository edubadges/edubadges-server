from rest_framework import permissions


class IsSocialAccountOwner(permissions.BasePermission):
    """
    Allows only owners of an object to read or write it via the API
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user