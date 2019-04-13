from rest_framework import permissions


class ObjectWithinScope(permissions.BasePermission):
    
    def has_object_permission(self, request, view, object):
        if request.user.has_perm('badgeuser.has_institution_scope'):
            if request.user.institution:
                return request.user.institution == object.get_institution()
        if request.user.has_perm('badgeuser.has_faculty_scope'):
            if request.user.faculty:
                return request.user.faculty == object.get_faculty()
        return False
