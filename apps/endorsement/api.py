from rest_framework.response import Response

from endorsement.models import Endorsement
from endorsement.serializer import EndorsementSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker


class EndorsementList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    serializer_class = EndorsementSerializer
    http_method_names = ['post']


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
        elif status == Endorsement.STATUS_ACCEPTED:
            print("TODO send mail")
            # EmailMessageMaker.create_endorsement_requested_mail()
        elif status == Endorsement.STATUS_REJECTED:
            print("TODO send mail")
            # EmailMessageMaker.create_endorsement_rejected_mail()
        endorsement.save()
        endorsement.endorsee.remove_cached_data(['cached_endorsements'])
        endorsement.endorser.remove_cached_data(['cached_endorsed'])
        return Response({"result": "ok"}, status=status.HTTP_200_OK)
