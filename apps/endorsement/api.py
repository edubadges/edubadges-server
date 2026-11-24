from endorsement.models import Endorsement
from endorsement.serializer import EndorsementSerializer
from entity.api import BaseEntityDetailView, BaseEntityListView, VersionedObjectMixin
from mainsite.exceptions import BadgrValidationError
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from rest_framework import status
from rest_framework.response import Response


class EndorsementList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ["post"]

    def post(self, request, **kwargs):
        serializer = EndorsementSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EndorsementDetail(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ["delete", "put"]
    permission_map = {"PUT": "may_award"}
    model = Endorsement

    def put(self, request, **kwargs):
        endorsement = Endorsement.objects.get(entity_id=kwargs["entity_id"])
        user = request.user
        endorser_permissions = endorsement.endorser.get_permissions(user)
        endorsee_permissions = endorsement.endorsee.get_permissions(user)
        if not endorser_permissions["may_award"] and not endorsee_permissions["may_award"]:
            raise BadgrValidationError("Insufficient permission", 999)
        new_status = request.data["status"]
        endorsement.status = new_status
        if new_status == Endorsement.STATUS_REVOKED:
            endorsement.revocation_reason = request.data["revocation_reason"]
        elif new_status == Endorsement.STATUS_REJECTED:
            endorsement.rejection_reason = request.data["rejection_reason"]
        endorsement.save()
        endorsement.clear_endorsement_cache()
        return Response({}, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        endorsement = Endorsement.objects.get(entity_id=kwargs["entity_id"])
        permissions = endorsement.endorsee.get_permissions(request.user)
        if not permissions["may_update"]:
            raise BadgrValidationError("Insufficient permission", 999)

        endorsement.clear_endorsement_cache()
        endorsement.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
