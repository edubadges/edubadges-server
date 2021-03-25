from rest_framework.response import Response
from rest_framework import status

from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from directaward.serializer import DirectAwardSerializer
from directaward.models import DirectAward
from directaward.permissions import IsDirectAwardOwner
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.permissions import HasObjectPermission

from entity.utils import validate_errors


class DirectAwardList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a new Direct Award
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)   # permissioned in serializer
    v1_serializer_class = DirectAwardSerializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    def post(self, request, **kwargs):
        """
        POST a new entity to be owned by the authenticated user
        """
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(many=True, data=request.data, context=context)
        validate_errors(serializer)

        new_instance = serializer.save(created_by=request.user)
        self.log_create(new_instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DirectAwardDetail(BaseEntityDetailView):
    model = DirectAward
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = DirectAwardSerializer
    http_method_names = ['put', 'delete']
    permission_map = {'PUT': 'may_award', 'DELETE': 'may_award'}


class DirectAwardAccept(BaseEntityDetailView):
    model = DirectAward  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsDirectAwardOwner)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        directaward = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, directaward):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get('accept', False):
            assertion = directaward.award()
            directaward.delete()
            return Response({'entity_id': assertion.entity_id}, status=status.HTTP_201_CREATED)
        directaward.reject()
        return Response({'rejected': True}, status=status.HTTP_200_OK)
