from rest_framework import permissions


class HasObjectPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        object_permission_required_for_method = view.permission_map[request.method]
        permissions = obj.get_permissions(request.user)
        if not permissions:
            return False
        return permissions[object_permission_required_for_method]


class StaffMembershipWithinScope(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff_membership_within_scope(obj)
