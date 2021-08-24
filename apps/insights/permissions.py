from rest_framework import permissions


class TeachPermission(permissions.BasePermission):
    """
    Allows access only to teachers
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_teacher
