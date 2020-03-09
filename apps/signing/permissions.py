from rest_framework import permissions


class MaySignAssertions(permissions.BasePermission):
    def has_permission(selfs, request, view):
        raise NotImplementedError


class OwnsSymmetricKey(permissions.BasePermission):
    def has_object_permission(self, request, view, symmetric_key):
        if symmetric_key:
            return symmetric_key.user == request.user
        else:
            return True

