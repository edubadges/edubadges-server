from rest_framework import permissions
from issuer.models import Issuer


class IssuerWithinUserScope(permissions.BasePermission):
    """
    When creating an LTI Client check to see if the POSTed or PUTted issuer slug is within user's scope
    """

    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        issuer = Issuer.objects.get(entity_id=request.data.get('issuer_slug', None))
        return request.user.within_scope(issuer)