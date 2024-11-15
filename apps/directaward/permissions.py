from rest_framework import permissions


class IsDirectAwardOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        from directaward.models import DirectAwardBundle
        user = request.user
        return obj.eppn in user.eppns or (
                    obj.recipient_email == user.email and obj.bundle.identifier_type == DirectAwardBundle.IDENTIFIER_EMAIL)
