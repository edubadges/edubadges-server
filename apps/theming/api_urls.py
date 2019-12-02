# encoding: utf-8


from django.conf.urls import url

from .api import GetTheme

urlpatterns = [
    url(r'^theme/(?P<subdomain>[^/]+)$', GetTheme.as_view(), name='v2_api_get_theme'),
]
