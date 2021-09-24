from rest_framework import permissions


class IsSocialAccountOwner(permissions.BasePermission):
    """
    Only grant access to owner of SocialAccount.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsSuperUser(permissions.BasePermission):
    """
    Allows access only to teachers
    """

    def has_permission(self, request, view):
        return request.user and hasattr(request.user, 'is_superuser') and request.user.is_superuser
