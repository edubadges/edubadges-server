from rest_framework import permissions

from entity.api import BaseEntityDetailView
from institution.models import Institution

from .serializers import PublicInstitutionSerializer


class PublicInstitutionDetail(BaseEntityDetailView):
    """
    PUT to edit an institution
    """
    model = Institution
    v1_serializer_class = PublicInstitutionSerializer
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['get']