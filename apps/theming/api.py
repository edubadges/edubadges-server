# encoding: utf-8
from entity.api import BaseEntityDetailView
from theming.models import Theme
from theming.serializers_v2 import ThemeSerializer


class GetTheme(BaseEntityDetailView):

    v2_serializer_class = ThemeSerializer

    def get_object(self, request, **kwargs):
        theme = Theme.objects.get(subdomain=kwargs['subdomain'])
        return theme

    def check_permissions(self, request):
        return True







