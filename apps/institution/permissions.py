from rest_framework import permissions


class UserHasInstitutionScope(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.has_perm('badgeuser.has_institution_scope'):
            return True
        return False
