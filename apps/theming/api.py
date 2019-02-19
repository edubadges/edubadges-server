# encoding: utf-8
from django.contrib.sites.models import Site

from entity.api import BaseEntityDetailView
from theming.models import Theme
from theming.serializers_v2 import ThemeSerializer


class GetTheme(BaseEntityDetailView):

    v2_serializer_class = ThemeSerializer

    def get_object(self, request, **kwargs):
        site = Site.objects.get(domain=kwargs['subdomain'])
        theme = site.theme
        return theme

    def check_permissions(self, request):
        return True







