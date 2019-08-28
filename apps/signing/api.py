from entity.api import BaseEntityDetailView
from signing.models import SymmetricKey
from signing.permissions import MaySignAssertions
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class SymmetricKeyView(BaseEntityDetailView):
    model = SymmetricKey
    http_method_names = ['post']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)

    def post(self, request, **kwargs):
        """
        Add password to create a SymmetricKey for this user
        """
        raise NotImplementedError