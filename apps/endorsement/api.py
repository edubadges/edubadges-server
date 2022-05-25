from rest_framework.response import Response

from endorsement.models import Endorsement
from endorsement.serializer import EndorsementSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class EndorsementList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    serializer_class = EndorsementSerializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}


class EndorsementDetail(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['delete', 'put']
    permission_map = {'PUT': 'may_award'}

    def put(self, request, **kwargs):
        endorsement = Endorsement.objects.get(entity_id=request.data['entity_id'])
        status = request.data['status']
        endorsement.status = status
        if status == Endorsement.STATUS_REVOKED:
            revocation_reason = request.data['revocation_reason']
            endorsement.revocation_reason = revocation_reason
        endorsement.save()
        endorsement.endorsee.remove_cached_data(['cached_endorsees'])
        endorsement.endorser.remove_cached_data(['cached_endorsements'])
        return Response({"result": "ok"}, status=status.HTTP_200_OK)
