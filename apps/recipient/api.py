# Created by wiggins@concentricsky.com on 3/31/16.

from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView
from issuer.models import Issuer
from issuer.permissions import IsEditor, IsIssuerEditor
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from recipient.models import RecipientGroup
from recipient.serializers_v1 import RecipientGroupSerializerV1, IssuerRecipientGroupListSerializerV1
from recipient.serializers_v2 import RecipientGroupSerializerV2

_TRUE_VALUES = ['true','t','on','yes','y','1',1,1.0,True]
_FALSE_VALUES = ['false','f','off','no','n','0',0,0.0,False]


def _scrub_boolean(boolean_str, default=None):
    if boolean_str in _TRUE_VALUES:
        return True
    if boolean_str in _FALSE_VALUES:
        return False
    return default


class IssuerRecipientGroupList(BaseEntityDetailView, VersionedObjectMixin):
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor)
    v1_serializer_class = IssuerRecipientGroupListSerializerV1
    v2_serializer_class = RecipientGroupSerializerV2

    def get_objects(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)
        return issuer.cached_recipient_groups()

    def get_context_data(self, **kwargs):
        context = super(IssuerRecipientGroupList, self).get_context_data(**kwargs)
        context['issuer'] = self.get_object(self.request, **kwargs)
        context['embed_recipients'] = _scrub_boolean(self.request.query_params.get('embedRecipients', False))
        return context

    def get(self, request, **kwargs):
        """
        GET a list of Recipient Groups owned by an Issuer
        ---
        parameters:
            - name: embedRecipients
              description: Whether or not to include Recipient Profiles information
              required: false
              default: false
              type: boolean
              paramType: query
        """
        return super(IssuerRecipientGroupList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        """
        Define a new Recipient Group
        """
        return super(IssuerRecipientGroupList, self).post(request, **kwargs)


class RecipientGroupDetail(BaseEntityDetailView):
    model = RecipientGroup
    permission_classes = (AuthenticatedWithVerifiedEmail, IsIssuerEditor)
    v1_serializer_class = RecipientGroupSerializerV1
    v2_serializer_class = RecipientGroupSerializerV2

    def get_context_data(self, **kwargs):
        context = super(RecipientGroupDetail, self).get_context_data(**kwargs)
        context['embed_recipients'] = _scrub_boolean(self.request.query_params.get('embedRecipients', False))
        context['recipient_group'] = self.get_object(self.request, **kwargs)
        return context

    def get(self, request, **kwargs):
        """
        GET detailed information about a Recipient Group
        ---
        parameters:
            - name: embedRecipients
              description: Whether or not to include Recipient Profiles information
              required: false
              default: false
              type: boolean
              paramType: query
        """
        return super(RecipientGroupDetail, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        """
        DELETE a Recipient Group
        """
        return super(RecipientGroupDetail, self).delete(request, **kwargs)

    def put(self, request, **kwargs):
        """
        Update an existing Recipient Group
        """
        return super(RecipientGroupDetail, self).put(request, **kwargs)



