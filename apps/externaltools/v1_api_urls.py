# encoding: utf-8


from django.conf.urls import url

from externaltools.api import ExternalToolList, ExternalToolLaunch

urlpatterns = [
    url(r'^$', ExternalToolList.as_view(), name='v1_api_externaltools_list'),
    url(r'^launch/(?P<slug>[^/]+)/(?P<launchpoint>[^/]+)$', ExternalToolLaunch.as_view(), name='v1_api_externaltools_launch'),
]