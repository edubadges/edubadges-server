# encoding: utf-8

from entity.api import BaseEntityDetailView
from theming.serializers_v2 import ThemeSerializer
from theming.utils import get_theme


class GetTheme(BaseEntityDetailView):

    v1_serializer_class = ThemeSerializer

    def get_object(self, request, **kwargs):
        return get_theme(request)

    def check_permissions(self, request):
        return True







