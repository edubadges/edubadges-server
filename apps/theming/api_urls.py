# encoding: utf-8


from django.urls import path

from .api import GetTheme

urlpatterns = [
    path('theme/<str:subdomain>', GetTheme.as_view(), name='v2_api_get_theme'),
]
