from rest_framework import permissions

class MaySignAssertions(permissions.BasePermission):
    def has_permission(selfs, request, view):
        return request.user.has_perm('signing.may_sign_assertions')

