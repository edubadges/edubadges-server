from django.conf.urls import url

from badge_connect.api import BadgeConnectView

urlpatterns = [
    url(r'^validate/(?P<entity_id>[^/]+)$', BadgeConnectView.as_view(), name='api_badge_connect'),
]
