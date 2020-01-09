# # encoding: utf-8
#
#
# from django.conf.urls import url
#
# from externaltools.api import ExternalToolList, ExternalToolLaunch
#
# urlpatterns = [
#     url(r'^$', ExternalToolList.as_view(), name='v2_api_externaltools_list'),
#     url(r'^launch/(?P<entity_id>[^/]+)/(?P<launchpoint>[^/]+)$', ExternalToolLaunch.as_view(), name='v2_api_externaltools_launch'),
# ]
