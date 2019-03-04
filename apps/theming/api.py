# encoding: utf-8
from django.contrib.sites.models import Site

from entity.api import BaseEntityDetailView
from mainsite.models import BadgrApp
from theming.models import Theme
from theming.serializers_v2 import ThemeSerializer
from theming.utils import get_theme


class GetTheme(BaseEntityDetailView):

    v2_serializer_class = ThemeSerializer

    def get_object(self, request, **kwargs):
        return get_theme(request)

    def check_permissions(self, request):
        return True







